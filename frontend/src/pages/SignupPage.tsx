import { useState, useRef, useCallback, useEffect } from "react"
import { Link } from "react-router-dom"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { toast } from "sonner"
import { Mail, CheckCircle, Eye, EyeOff } from "lucide-react"
import { signupStart } from "@/api/services/auth"
import { ApiError } from "@/lib/api/errors"

// ---------------------------------------------------------------------------
// Zod schema with confirm_password match validation
// ---------------------------------------------------------------------------

const signupSchema = z
  .object({
    company_name: z.string().min(1, "Company name is required").max(200),
    primary_contact: z.string().min(1, "Primary contact is required").max(200),
    admin_email: z.string().min(1, "Email is required").email("Invalid email address"),
    password: z
      .string()
      .min(8, "Password must be at least 8 characters")
      .max(128),
    confirm_password: z.string().min(1, "Please confirm your password"),
    phone: z.string().max(30).optional().or(z.literal("")),
    location: z.string().max(200).optional().or(z.literal("")),
    accept_terms: z.boolean().refine((val) => val === true, {
      message: "You must accept the terms and conditions",
    }),
  })
  .refine((data) => data.password === data.confirm_password, {
    message: "Passwords do not match",
    path: ["confirm_password"],
  })

type SignupFormValues = z.infer<typeof signupSchema>

// ---------------------------------------------------------------------------
// Turnstile site key
// ---------------------------------------------------------------------------

const TURNSTILE_SITE_KEY =
  (import.meta as any)?.env?.VITE_TURNSTILE_SITE_KEY || "1x00000000000000000000AA" // invisible-always-pass key for dev

interface ConfirmationState {
  email: string
  message: string
  expiresInMinutes: number
}

export function SignupPage() {
  const [confirmation, setConfirmation] = useState<ConfirmationState | null>(null)
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  const [turnstileToken, setTurnstileToken] = useState<string | null>(null)
  const [turnstileReady, setTurnstileReady] = useState(false)
  const turnstileRef = useRef<HTMLDivElement>(null)
  const turnstileWidgetId = useRef<string | undefined>(undefined)

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    setValue,
    setError,
  } = useForm<SignupFormValues>({
    resolver: zodResolver(signupSchema),
    defaultValues: {
      company_name: "",
      primary_contact: "",
      admin_email: "",
      password: "",
      confirm_password: "",
      phone: "",
      location: "",
      accept_terms: false,
    },
  })

  // ---------------------------------------------------------------------------
  // Cloudflare Turnstile — load script and render widget
  // ---------------------------------------------------------------------------

  const renderTurnstile = useCallback(() => {
    if (
      !turnstileRef.current ||
      typeof window === "undefined" ||
      !(window as any).turnstile
    )
      return

    // Avoid double-render
    if (turnstileWidgetId.current) {
      ;(window as any).turnstile.reset(turnstileWidgetId.current)
      return
    }

    turnstileWidgetId.current = (window as any).turnstile.render(
      turnstileRef.current,
      {
        sitekey: TURNSTILE_SITE_KEY,
        callback: (token: string) => {
          setTurnstileToken(token)
        },
        "expired-callback": () => {
          setTurnstileToken(null)
        },
        "error-callback": () => {
          setTurnstileToken(null)
        },
      }
    )
    setTurnstileReady(true)
  }, [])

  useEffect(() => {
    // If Turnstile script already loaded, render immediately
    if ((window as any).turnstile) {
      renderTurnstile()
      return
    }

    // Otherwise inject the script
    const script = document.createElement("script")
    script.src = "https://challenges.cloudflare.com/turnstile/v0/api.js"
    script.async = true
    script.defer = true
    script.onload = renderTurnstile
    document.body.appendChild(script)

    return () => {
      // Cleanup widget on unmount
      if (turnstileWidgetId.current && (window as any).turnstile) {
        ;(window as any).turnstile.remove(turnstileWidgetId.current)
        turnstileWidgetId.current = undefined
      }
    }
  }, [renderTurnstile])

  // ---------------------------------------------------------------------------
  // Form submission
  // ---------------------------------------------------------------------------

  async function onSubmit(data: SignupFormValues) {
    try {
      // Validate Turnstile token
      if (!turnstileToken && TURNSTILE_SITE_KEY !== "1x00000000000000000000AA") {
        toast.error("Please complete the security check")
        return
      }

      const payload = {
        company_name: data.company_name,
        primary_contact: data.primary_contact,
        admin_email: data.admin_email,
        password: data.password,
        phone: data.phone || null,
        location: data.location || null,
        bidder_display_name: null,
        accept_terms: data.accept_terms,
        cf_turnstile_token: turnstileToken || null,
      }
      const response = await signupStart(payload)
      setConfirmation({
        email: response.email,
        message: response.message,
        expiresInMinutes: response.expires_in_minutes,
      })
    } catch (e: unknown) {
      if (e instanceof ApiError) {
        // Extract field-level errors from FastAPI validation error shape
        // e.g. { detail: [{ loc: ["body", "admin_email"], msg: "...", type: "..." }] }
        const details = e.details as Record<string, unknown> | undefined
        if (details && Array.isArray(details.detail)) {
          const fieldErrors = details.detail as Array<{
            loc?: string[]
            msg?: string
          }>
          let hasFieldError = false
          for (const err of fieldErrors) {
            const loc = err.loc ?? []
            // loc[0]="body", loc[1]=field_name
            const field = loc.length >= 2 ? loc[1] : null
            if (field && err.msg) {
              // Map backend field name to form field name
              const formField = field === "admin_email" ? "admin_email" : field
              if (formField in data) {
                setError(formField as any, { message: err.msg })
                hasFieldError = true
              }
            }
          }
          if (!hasFieldError) {
            const firstMsg = fieldErrors[0]?.msg
            toast.error(firstMsg || "Validation failed")
          }
        } else if (details && typeof details.detail === "string") {
          toast.error(details.detail)
        } else {
          toast.error(e.message)
        }
      } else {
        const message = e instanceof Error ? e.message : "Signup failed"
        toast.error(message)
      }
    }
  }

  // ---------------------------------------------------------------------------
  // Confirmation screen
  // ---------------------------------------------------------------------------

  if (confirmation) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="w-full max-w-sm border rounded-xl p-8 bg-card shadow-sm text-center">
          <div className="flex justify-center mb-4">
            <div className="rounded-full bg-primary/10 p-3">
              <CheckCircle className="h-8 w-8 text-primary" />
            </div>
          </div>
          <h1 className="text-xl font-semibold mb-2">Check your email</h1>
          <p className="text-sm text-muted-foreground mb-4">
            {confirmation.message}
          </p>
          <div className="flex items-center justify-center gap-2 text-sm text-muted-foreground mb-6">
            <Mail className="h-4 w-4" />
            <span>Sent to {confirmation.email}</span>
          </div>
          <p className="text-xs text-muted-foreground mb-6">
            This link expires in {confirmation.expiresInMinutes} minutes.
          </p>
          <Link
            to="/login"
            className="inline-flex items-center justify-center w-full py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:opacity-90 transition-opacity"
          >
            Return to Sign In
          </Link>
        </div>
      </div>
    )
  }

  // ---------------------------------------------------------------------------
  // Signup form
  // ---------------------------------------------------------------------------

  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <div className="w-full max-w-sm border rounded-xl p-8 bg-card shadow-sm">
        <h1 className="text-xl font-semibold mb-1">VeloBid</h1>
        <p className="text-sm text-muted-foreground mb-6">Create your enterprise account</p>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
          {/* Company Name */}
          <div>
            <label htmlFor="company_name" className="block text-sm font-medium mb-1">
              Company name
            </label>
            <input
              id="company_name"
              type="text"
              autoComplete="organization"
              {...register("company_name")}
              className="w-full px-3 py-2 border rounded-lg text-sm bg-background"
              placeholder="Enter your company name"
            />
            {errors.company_name && (
              <p className="text-xs text-destructive mt-1" role="alert">
                {errors.company_name.message}
              </p>
            )}
          </div>

          {/* Primary Contact */}
          <div>
            <label htmlFor="primary_contact" className="block text-sm font-medium mb-1">
              Primary contact
            </label>
            <input
              id="primary_contact"
              type="text"
              autoComplete="name"
              {...register("primary_contact")}
              className="w-full px-3 py-2 border rounded-lg text-sm bg-background"
              placeholder="Full name of primary contact"
            />
            {errors.primary_contact && (
              <p className="text-xs text-destructive mt-1" role="alert">
                {errors.primary_contact.message}
              </p>
            )}
          </div>

          {/* Admin Email */}
          <div>
            <label htmlFor="admin_email" className="block text-sm font-medium mb-1">
              Admin email
            </label>
            <input
              id="admin_email"
              type="email"
              autoComplete="email"
              {...register("admin_email")}
              className="w-full px-3 py-2 border rounded-lg text-sm bg-background"
              placeholder="admin@company.com"
            />
            {errors.admin_email && (
              <p className="text-xs text-destructive mt-1" role="alert">
                {errors.admin_email.message}
              </p>
            )}
          </div>

          {/* Password with show/hide toggle */}
          <div>
            <label htmlFor="password" className="block text-sm font-medium mb-1">
              Password
            </label>
            <div className="relative">
              <input
                id="password"
                type={showPassword ? "text" : "password"}
                autoComplete="new-password"
                {...register("password")}
                className="w-full px-3 py-2 pr-10 border rounded-lg text-sm bg-background"
                placeholder="Minimum 8 characters"
              />
              <button
                type="button"
                onClick={() => setShowPassword((v) => !v)}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground p-1"
                aria-label={showPassword ? "Hide password" : "Show password"}
                tabIndex={-1}
              >
                {showPassword ? (
                  <EyeOff className="h-4 w-4" />
                ) : (
                  <Eye className="h-4 w-4" />
                )}
              </button>
            </div>
            {errors.password && (
              <p className="text-xs text-destructive mt-1" role="alert">
                {errors.password.message}
              </p>
            )}
          </div>

          {/* Confirm Password with show/hide toggle */}
          <div>
            <label htmlFor="confirm_password" className="block text-sm font-medium mb-1">
              Confirm password
            </label>
            <div className="relative">
              <input
                id="confirm_password"
                type={showConfirmPassword ? "text" : "password"}
                autoComplete="new-password"
                {...register("confirm_password")}
                className="w-full px-3 py-2 pr-10 border rounded-lg text-sm bg-background"
                placeholder="Re-enter password"
              />
              <button
                type="button"
                onClick={() => setShowConfirmPassword((v) => !v)}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground p-1"
                aria-label={showConfirmPassword ? "Hide confirm password" : "Show confirm password"}
                tabIndex={-1}
              >
                {showConfirmPassword ? (
                  <EyeOff className="h-4 w-4" />
                ) : (
                  <Eye className="h-4 w-4" />
                )}
              </button>
            </div>
            {errors.confirm_password && (
              <p className="text-xs text-destructive mt-1" role="alert">
                {errors.confirm_password.message}
              </p>
            )}
          </div>

          {/* Phone (optional) */}
          <div>
            <label htmlFor="phone" className="block text-sm font-medium mb-1">
              Phone <span className="text-muted-foreground">(optional)</span>
            </label>
            <input
              id="phone"
              type="tel"
              autoComplete="tel"
              {...register("phone")}
              className="w-full px-3 py-2 border rounded-lg text-sm bg-background"
              placeholder="+1 (555) 123-4567"
            />
            {errors.phone && (
              <p className="text-xs text-destructive mt-1" role="alert">
                {errors.phone.message}
              </p>
            )}
          </div>

          {/* Location (optional) — split autoComplete hints */}
          <div>
            <label htmlFor="location" className="block text-sm font-medium mb-1">
              Location <span className="text-muted-foreground">(optional)</span>
            </label>
            <input
              id="location"
              type="text"
              autoComplete="address-level2"
              {...register("location")}
              className="w-full px-3 py-2 border rounded-lg text-sm bg-background"
              placeholder="City, State"
            />
            {errors.location && (
              <p className="text-xs text-destructive mt-1" role="alert">
                {errors.location.message}
              </p>
            )}
          </div>

          {/* Accept Terms */}
          <div className="flex items-start gap-2">
            <input
              type="checkbox"
              id="accept_terms"
              {...register("accept_terms")}
              className="mt-1 h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary"
            />
            <label htmlFor="accept_terms" className="text-sm text-muted-foreground">
              I accept the{" "}
              <Link
                to="/terms"
                className="text-primary underline-offset-4 hover:underline"
              >
                terms and conditions
              </Link>{" "}
              and{" "}
              <Link
                to="/privacy"
                className="text-primary underline-offset-4 hover:underline"
              >
                privacy policy
              </Link>
            </label>
          </div>
          {errors.accept_terms && (
            <p className="text-xs text-destructive" role="alert">
              {errors.accept_terms.message}
            </p>
          )}

          {/* Turnstile widget */}
          <div ref={turnstileRef} className="flex justify-center min-h-[65px]" />

          {/* Submit */}
          <button
            type="submit"
            disabled={isSubmitting || (!turnstileReady && TURNSTILE_SITE_KEY !== "1x00000000000000000000AA")}
            className="w-full py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:opacity-90 disabled:opacity-50"
          >
            {isSubmitting ? "Creating account..." : "Create Account"}
          </button>
        </form>

        {/* Link to Login */}
        <p className="text-sm text-muted-foreground text-center mt-6">
          Already have an account?{" "}
          <Link to="/login" className="text-primary underline-offset-4 hover:underline">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  )
}
