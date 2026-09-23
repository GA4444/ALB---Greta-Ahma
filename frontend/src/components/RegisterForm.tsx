import { FormEvent, useId, useRef, useState } from 'react'
import { register } from '../api'
import './RegisterForm.css'

export type RegisterFormProps = {
	onSuccess: (username: string) => void
	onSwitchToLogin: () => void
	onMessage?: (message: string) => void
}

type RegisterFields = {
	firstName: string
	lastName: string
	username: string
	email: string
	age: string
	password: string
	confirmPassword: string
}

type FieldKey = keyof RegisterFields
type FieldErrors = Partial<Record<FieldKey, string>>

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/i

const emptyFields = (): RegisterFields => ({
	firstName: '',
	lastName: '',
	username: '',
	email: '',
	age: '',
	password: '',
	confirmPassword: '',
})

const FIELD_ORDER: FieldKey[] = [
	'firstName',
	'lastName',
	'username',
	'email',
	'age',
	'password',
	'confirmPassword',
]

function validateField(name: FieldKey, values: RegisterFields): string {
	const v = values[name]

	switch (name) {
		case 'firstName':
			if (!v.trim()) return 'Ju lutem shkruani emrin tuaj.'
			if (v.trim().length < 2) return 'Emri duhet të ketë të paktën 2 shkronja.'
			return ''
		case 'lastName':
			if (!v.trim()) return 'Ju lutem shkruani mbiemrin tuaj.'
			if (v.trim().length < 2) return 'Mbiemri duhet të ketë të paktën 2 shkronja.'
			return ''
		case 'username':
			if (!v.trim()) return 'Ju lutem shkruani emrin e përdoruesit.'
			if (/\s/.test(v)) return 'Emri i përdoruesit nuk duhet të ketë hapësira.'
			if (v.trim().length < 3) return 'Emri i përdoruesit duhet të ketë të paktën 3 karaktere.'
			return ''
		case 'email':
			if (!v.trim()) return 'Ju lutem shkruani email-in tuaj.'
			if (!EMAIL_RE.test(v.trim())) return 'Ju lutem vendosni një adresë email-i të vlefshme.'
			return ''
		case 'age': {
			if (!v.trim()) return ''
			const n = Number(v)
			if (!Number.isFinite(n) || !Number.isInteger(n)) return 'Mosha duhet të jetë një numër i plotë.'
			if (n < 5 || n > 80) return 'Mosha duhet të jetë midis 5 dhe 80.'
			return ''
		}
		case 'password':
			if (!v) return 'Ju lutem krijoni një fjalëkalim.'
			if (v.length < 8) return 'Fjalëkalimi duhet të përmbajë të paktën 8 karaktere.'
			return ''
		case 'confirmPassword':
			if (!v) return 'Ju lutem konfirmoni fjalëkalimin.'
			if (v !== values.password) return 'Fjalëkalimet nuk përputhen.'
			return ''
		default:
			return ''
	}
}

function validateAll(values: RegisterFields): FieldErrors {
	const next: FieldErrors = {}
	for (const key of FIELD_ORDER) {
		const err = validateField(key, values)
		if (err) next[key] = err
	}
	return next
}

function mapServerError(error: unknown): { field?: FieldKey; message: string } {
	const e = error as {
		response?: { status?: number; data?: { detail?: unknown } }
		message?: string
		code?: string
	}
	const status = e?.response?.status
	const detail = e?.response?.data?.detail
	const detailText = typeof detail === 'string' ? detail : ''

	const usernameTaken =
		(/username|përdorues|zënë|already registered/i.test(detailText) && !/email/i.test(detailText)) ||
		(status === 409 && /username/i.test(detailText))

	if (usernameTaken) {
		return {
			field: 'username',
			message: 'Ky emër përdoruesi është tashmë i zënë. Ju lutem zgjidhni një tjetër.',
		}
	}

	const emailTaken =
		status === 409 ||
		/email/i.test(detailText) ||
		/ekziston tashmë/i.test(detailText) ||
		/already.*email|email.*already/i.test(detailText)

	if (emailTaken) {
		return {
			field: 'email',
			message:
				'Ky email është tashmë i regjistruar. Ju lutem përdorni një email tjetër ose hyni në llogarinë tuaj.',
		}
	}

	if (
		e?.code === 'ECONNREFUSED' ||
		e?.code === 'ECONNABORTED' ||
		/network|timeout/i.test(e?.message || '')
	) {
		return { message: 'Nuk u lidh me serverin. Ju lutem provoni përsëri pas një çasti.' }
	}

	return { message: detailText || 'Diçka nuk shkoi mirë. Ju lutem provoni përsëri.' }
}

export default function RegisterForm({ onSuccess, onSwitchToLogin, onMessage }: RegisterFormProps) {
	const formId = useId()
	const [values, setValues] = useState<RegisterFields>(emptyFields)
	const [errors, setErrors] = useState<FieldErrors>({})
	const [formError, setFormError] = useState('')
	const [submitting, setSubmitting] = useState(false)
	const submittingRef = useRef(false)
	const fieldRefs = useRef<Partial<Record<FieldKey, HTMLInputElement | null>>>({})

	const setField = (name: FieldKey, raw: string) => {
		const value = name === 'username' ? raw.replace(/\s/g, '') : raw
		setValues((prev) => {
			const next = { ...prev, [name]: value }
			setErrors((errs) => {
				if (!errs[name] && name !== 'password' && name !== 'confirmPassword') return errs
				const updated = { ...errs }
				const fieldErr = validateField(name, next)
				if (fieldErr) updated[name] = fieldErr
				else delete updated[name]
				if (name === 'password' && next.confirmPassword) {
					const confirmErr = validateField('confirmPassword', next)
					if (confirmErr) updated.confirmPassword = confirmErr
					else delete updated.confirmPassword
				}
				return updated
			})
			return next
		})
		if (formError) setFormError('')
	}

	const handleBlur = (name: FieldKey) => {
		setErrors((prev) => {
			const current = { ...values, [name]: values[name] }
			const err = validateField(name, current)
			const next = { ...prev }
			if (err) next[name] = err
			else delete next[name]
			return next
		})
	}

	const focusFirstError = (errs: FieldErrors) => {
		for (const key of FIELD_ORDER) {
			if (errs[key]) {
				fieldRefs.current[key]?.focus()
				return
			}
		}
	}

	const handleSubmit = async (e: FormEvent) => {
		e.preventDefault()
		if (submittingRef.current) return

		const nextErrors = validateAll(values)
		setErrors(nextErrors)

		if (Object.keys(nextErrors).length > 0) {
			const summary = 'Ju lutem plotësoni të gjitha fushat e kërkuara për të vazhduar.'
			setFormError(summary)
			onMessage?.(summary)
			focusFirstError(nextErrors)
			return
		}

		setFormError('')
		submittingRef.current = true
		setSubmitting(true)

		try {
			const username = values.username.trim()
			await register(
				values.firstName.trim(),
				values.lastName.trim(),
				username,
				values.email.trim(),
				values.password,
				values.age.trim() ? parseInt(values.age, 10) : undefined
			)
			setValues(emptyFields())
			setErrors({})
			onSuccess(username)
		} catch (err) {
			const mapped = mapServerError(err)
			if (mapped.field) {
				setErrors((prev) => ({ ...prev, [mapped.field!]: mapped.message }))
				fieldRefs.current[mapped.field]?.focus()
			}
			setFormError(mapped.message)
			onMessage?.(mapped.message)
		} finally {
			submittingRef.current = false
			setSubmitting(false)
		}
	}

	const renderField = (
		name: FieldKey,
		label: string,
		opts: {
			type?: string
			autoComplete?: string
			placeholder?: string
			helper?: string
			required?: boolean
			inputMode?: 'text' | 'email' | 'numeric' | 'tel' | 'search' | 'url' | 'none' | 'decimal'
		} = {}
	) => {
		const id = `${formId}-${name}`
		const errId = `${id}-error`
		const helpId = `${id}-help`
		const err = errors[name]
		const required = opts.required !== false && name !== 'age'

		return (
			<div className={`register-field${err ? ' has-error' : ''}`}>
				<label className="register-label" htmlFor={id}>
					{label}
					{required ? (
						<span className="register-required" aria-hidden="true">
							{' '}
							*
						</span>
					) : (
						<span className="register-optional"> (opsionale)</span>
					)}
				</label>
				<input
					ref={(el) => {
						fieldRefs.current[name] = el
					}}
					id={id}
					className={`auth-input register-input${err ? ' is-invalid' : ''}`}
					type={opts.type || 'text'}
					autoComplete={opts.autoComplete}
					placeholder={opts.placeholder}
					inputMode={opts.inputMode}
					value={values[name]}
					onChange={(ev) => setField(name, ev.target.value)}
					onBlur={() => handleBlur(name)}
					aria-invalid={Boolean(err)}
					aria-describedby={err ? errId : opts.helper ? helpId : undefined}
					aria-required={required}
					disabled={submitting}
				/>
				{opts.helper && !err && (
					<p id={helpId} className="register-helper">
						{opts.helper}
					</p>
				)}
				{err && (
					<p id={errId} className="register-error" role="alert">
						{err}
					</p>
				)}
			</div>
		)
	}

	return (
		<form
			className="auth-form enhanced-registration register-form"
			onSubmit={handleSubmit}
			noValidate
		>
			{formError && (
				<div className="register-form-alert" role="alert">
					{formError}
				</div>
			)}

			<div className="form-row">
				{renderField('firstName', 'Emri', {
					autoComplete: 'given-name',
					placeholder: 'p.sh. Arta',
				})}
				{renderField('lastName', 'Mbiemri', {
					autoComplete: 'family-name',
					placeholder: 'p.sh. Krasniqi',
				})}
			</div>

			<div className="form-row single-column">
				{renderField('username', 'Emri i përdoruesit', {
					autoComplete: 'username',
					placeholder: 'p.sh. arta_krasniqi',
					helper: 'Shkruaje bashkë, pa hapësira. Me këtë emër do të hysh herën tjetër.',
				})}
			</div>

			<div className="form-row single-column">
				{renderField('email', 'Email', {
					type: 'email',
					autoComplete: 'email',
					placeholder: 'p.sh. arta@email.com',
					inputMode: 'email',
				})}
			</div>

			<div className="form-row single-column">
				{renderField('age', 'Mosha', {
					type: 'number',
					placeholder: 'p.sh. 12',
					inputMode: 'numeric',
					required: false,
					helper: 'Opsionale — ndihmon për përshtatjen e ushtrimeve.',
				})}
			</div>

			<div className="form-row single-column">
				{renderField('password', 'Fjalëkalimi', {
					type: 'password',
					autoComplete: 'new-password',
					placeholder: 'Të paktën 8 karaktere',
					helper: 'Përdor të paktën 8 karaktere.',
				})}
			</div>

			<div className="form-row single-column">
				{renderField('confirmPassword', 'Konfirmo fjalëkalimin', {
					type: 'password',
					autoComplete: 'new-password',
					placeholder: 'Përsërit fjalëkalimin',
				})}
			</div>

			<button
				type="submit"
				className="auth-submit register-submit"
				disabled={submitting}
				aria-busy={submitting}
			>
				{submitting ? 'Duke u regjistruar…' : 'Regjistrohu'}
			</button>

			<p className="auth-switch-hint">
				Ke llogari?{' '}
				<button
					type="button"
					className="auth-switch-link"
					onClick={onSwitchToLogin}
					disabled={submitting}
				>
					Hyr
				</button>
			</p>
		</form>
	)
}
