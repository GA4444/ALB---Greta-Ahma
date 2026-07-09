"""
Train lightweight Deep-IRT/DKT models from AlbLingo attempt sequences.

Run on a training machine:
  pip install -r backend/requirements-training.txt
  cd backend
  python scripts/train_deep_irt_dkt.py
"""

import argparse
import json
import os
import sys
from datetime import datetime
from typing import Dict, List

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.database import SessionLocal  # noqa: E402
from app.models import Attempt  # noqa: E402
from app.services.albanian_research_ai import deep_learning_sequence_dataset  # noqa: E402


def require_torch():
    try:
        import torch  # noqa: F401
    except Exception as exc:
        raise SystemExit(
            "Missing torch. Install training dependencies on GPU/Colab:\n"
            "  pip install -r backend/requirements-training.txt\n"
            f"Original error: {exc}"
        )


def load_sequences() -> List[Dict]:
    db = SessionLocal()
    try:
        attempts = db.query(Attempt).order_by(Attempt.id.asc()).all()
        return deep_learning_sequence_dataset(attempts)["sequences"]
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="Train Deep-IRT/DKT sequence model.")
    parser.add_argument("--out", default="model_artifacts/deep_irt_dkt")
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--hidden", type=int, default=64)
    parser.add_argument("--min-seq", type=int, default=2)
    args = parser.parse_args()

    require_torch()
    import torch
    from torch import nn

    out_dir = os.path.abspath(os.path.join(BACKEND_DIR, args.out))
    os.makedirs(out_dir, exist_ok=True)
    sequences = [s for s in load_sequences() if s["sequence_length"] >= args.min_seq]
    if not sequences:
        raise SystemExit("Not enough attempt sequences for Deep-IRT/DKT. Collect more student attempts first.")

    users = sorted({s["user_id"] for s in sequences})
    exercises = sorted({int(a["exercise_id"]) for s in sequences for a in s["attempts"]})
    skills = sorted({a["skill"] for s in sequences for a in s["attempts"]})
    user_to_id = {user_id: i for i, user_id in enumerate(users)}
    exercise_to_id = {exercise_id: i for i, exercise_id in enumerate(exercises)}
    skill_to_id = {skill: i + 1 for i, skill in enumerate(skills)}
    n_skills = len(skill_to_id) + 1

    class DKT(nn.Module):
        def __init__(self, n_skills: int, hidden: int):
            super().__init__()
            self.embed = nn.Embedding(n_skills * 2, hidden)
            self.rnn = nn.GRU(hidden, hidden, batch_first=True)
            self.out = nn.Linear(hidden, n_skills)

        def forward(self, x):
            emb = self.embed(x)
            h, _ = self.rnn(emb)
            return self.out(h)

    class NeuralIRT(nn.Module):
        """Compact Deep-IRT style model using student, item and skill embeddings."""

        def __init__(self, n_users: int, n_items: int, n_skills: int, hidden: int):
            super().__init__()
            emb = max(8, hidden // 2)
            self.user_emb = nn.Embedding(n_users, emb)
            self.item_emb = nn.Embedding(n_items, emb)
            self.skill_emb = nn.Embedding(n_skills, emb)
            self.net = nn.Sequential(
                nn.Linear(emb * 3, hidden),
                nn.ReLU(),
                nn.Linear(hidden, 1),
            )

        def forward(self, user_ids, item_ids, skill_ids):
            x = torch.cat(
                [
                    self.user_emb(user_ids),
                    self.item_emb(item_ids),
                    self.skill_emb(skill_ids),
                ],
                dim=-1,
            )
            return self.net(x).squeeze(-1)

    model = DKT(n_skills=n_skills, hidden=args.hidden)
    irt_model = NeuralIRT(
        n_users=max(len(user_to_id), 1),
        n_items=max(len(exercise_to_id), 1),
        n_skills=n_skills,
        hidden=args.hidden,
    )
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    irt_opt = torch.optim.Adam(irt_model.parameters(), lr=1e-3)
    loss_fn = nn.BCEWithLogitsLoss()

    training_rows = []
    irt_rows = []
    for seq in sequences:
        attempts = seq["attempts"]
        user_idx = user_to_id[seq["user_id"]]
        for attempt in attempts:
            irt_rows.append((
                user_idx,
                exercise_to_id[int(attempt["exercise_id"])],
                skill_to_id.get(attempt["skill"], 0),
                float(attempt["correct"]),
            ))
        if len(attempts) < 2:
            continue
        x = []
        y_skill = []
        y_correct = []
        for current, nxt in zip(attempts[:-1], attempts[1:]):
            skill_id = skill_to_id.get(current["skill"], 0)
            x.append(skill_id + (n_skills if current["correct"] else 0))
            y_skill.append(skill_to_id.get(nxt["skill"], 0))
            y_correct.append(float(nxt["correct"]))
        training_rows.append((torch.tensor([x], dtype=torch.long), torch.tensor(y_skill), torch.tensor(y_correct)))

    for epoch in range(args.epochs):
        total = 0.0
        for x, y_skill, y_correct in training_rows:
            opt.zero_grad()
            logits = model(x)[0, torch.arange(len(y_skill)), y_skill]
            loss = loss_fn(logits, y_correct)
            loss.backward()
            opt.step()
            total += float(loss.item())
        if epoch % 5 == 0:
            print(f"epoch={epoch} loss={total / max(len(training_rows), 1):.4f}")

    for epoch in range(args.epochs):
        total = 0.0
        for user_id, item_id, skill_id, correct in irt_rows:
            irt_opt.zero_grad()
            logit = irt_model(
                torch.tensor([user_id], dtype=torch.long),
                torch.tensor([item_id], dtype=torch.long),
                torch.tensor([skill_id], dtype=torch.long),
            )
            loss = loss_fn(logit, torch.tensor([correct], dtype=torch.float))
            loss.backward()
            irt_opt.step()
            total += float(loss.item())
        if epoch % 5 == 0:
            print(f"irt_epoch={epoch} loss={total / max(len(irt_rows), 1):.4f}")

    torch.save(model.state_dict(), os.path.join(out_dir, "dkt_model.pt"))
    torch.save(irt_model.state_dict(), os.path.join(out_dir, "deep_irt_model.pt"))
    manifest = {
        "trained_at_utc": datetime.utcnow().isoformat() + "Z",
        "model": "GRU-DKT plus compact Neural-IRT/Deep-IRT style baseline",
        "users": user_to_id,
        "exercises": exercise_to_id,
        "skills": skill_to_id,
        "sequence_count": len(sequences),
        "attempt_count": len(irt_rows),
        "artifacts": {
            "dkt": os.path.join(out_dir, "dkt_model.pt"),
            "deep_irt": os.path.join(out_dir, "deep_irt_model.pt"),
        },
        "note": "Use as first neural KT/IRT baseline; collect more attempts before reporting final scientific performance.",
    }
    with open(os.path.join(out_dir, "training_manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
