import { useState } from "react"
import { Link } from "react-router-dom"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { toast } from "sonner"
import { Mail, CheckCircle } from "lucide-react"
import { signupStart } from "@/api/services/auth"
import { ApiError } from "@/lib/api/errors"

const signupSchema = z.object({
  company_name: z.string().min(1, "Company name is required").max(200),
  primary_contact: z.string().min(1, "Primary contact is required").max(200),
  admin_email: z.string().min(1, "Email is required").email("Invalid email address"),
  password: z.string().min(8, "Password must be at least 8 characters").max(128),
  phone: z.string().max(30).optional().or(z.literal("")),
  location: z.string().max(200).optional().or(z.literal("")),
  accept_terms: z.boolean().refine((val) => val === true, {
    message: "You must accept the terms and conditions",
  }),
})

type SignupFormValues = z.infer<typeof signupSchema>

interface ConfirmationState {
  email: string
  message: string
  expiresInMinutes: number
}

export function SignupPage() {
  const [confirmation, setConfirmation] = useState<ConfirmationState | null>(null)

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<SignupFormValues>({
    resolver: zodResolver(signupSchema),
    defaultValues: {
      company_name: "",
      primary_contact: "",
      admin_email: "",
      password: "",
      phone: "",
      location: "",
      accept_terms: false,
    },
  })

  async function onSubmit(data: SignupFormValues) {
    try {
      const payload = {
        ...data,
        phone: data.phone || null,
        location: data.location || null,
        bidder_display_name: null,
      }
      const response = await signupStart(payload)
      setConfirmation({
        email: response.email,
        message: response.message,
        expiresInMinutes: response.expires_in_minutes,
      })
    } catch (e: unknown) {
      if (e instanceof ApiError) {
        if (e.details && typeof e.details === "object") {
          const details = e.details as Record<string, unknown>
          if (details.detail && typeof details.detail === "string") {
            toast.error(details.detail)
          } else {
            toast.error(e.message)
          }
        } else {
          toast.error(e.message)
        }
      } else {
        const message = e instanceof Error ? e.message : "Signup failed"
        toast.error(message)
      }
    }
  }

  // Confirmation screen after successful signup
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

  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <div className="w-full max-w-sm border rounded-xl p-8 bg-card shadow-sm">
        <h1 className="text-xl font-semibold mb-1">VeloBid</h1>
        <p className="text-sm text-muted-foreground mb-6">Create your enterprise account</p>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          {/* Company Name */}
          <div>
            <label className="block text-sm font-medium mb-1">Company name</label>
            <input
              type="text"
              {...register("company_name")}
              className="w-full px-3 py-2 border rounded-lg text-sm bg-background"
              placeholder="Enter your company name"
            />
            {errors.company_name && (
              <p className="text-xs text-destructive mt-1">{errors.company_name.message}</p>
            )}
          </div>

          {/* Primary Contact */}
          <div>
            <label className="block text-sm font-medium mb-1">Primary contact</label>
            <input
              type="text"
              {...register("primary_contact")}
              className="w-full px-3 py-2 border rounded-lg text-sm bg-background"
              placeholder="Full name of primary contact"
            />
            {errors.primary_contact && (
              <p className="text-xs text-destructive mt-1">{errors.primary_contact.message}</p>
            )}
          </div>

          {/* Admin Email */}
          <div>
            <label className="block text-sm font-medium mb-1">Admin email</label>
            <input
              type="email"
              {...register("admin_email")}
              className="w-full px-3 py-2 border rounded-lg text-sm bg-background"
              placeholder="admin@company.com"
            />
            {errors.admin_email && (
              <p className="text-xs text-destructive mt-1">{errors.admin_email.message}</p>
            )}
          </div>

          {/* Password */}
          <div>
            <label className="block text-sm font-medium mb-1">Password</label>
            <input
              type="password"
              {...register("password")}
              className="w-full px-3 py-2 border rounded-lg text-sm bg-background"
              placeholder="Minimum 8 characters"
            />
            {errors.password && (
              <p className="text-xs text-destructive mt-1">{errors.password.message}</p>
            )}
          </div>

          {/* Phone (optional) */}
          <div>
            <label className="block text-sm font-medium mb-1">
              Phone <span className="text-muted-foreground">(optional)</span>
            </label>
            <input
              type="tel"
              {...register("phone")}
              className="w-full px-3 py-2 border rounded-lg text-sm bg-background"
              placeholder="+1 (555) 123-4567"
            />
            {errors.phone && (
              <p className="text-xs text-destructive mt-1">{errors.phone.message}</p>
            )}
          </div>

          {/* Location (optional) */}
          <div>
            <label className="block text-sm font-medium mb-1">
              Location <span className="text-muted-foreground">(optional)</span>
            </label>
            <input
              type="text"
              {...register("location")}
              className="w-full px-3 py-2 border rounded-lg text-sm bg-background"
              placeholder="City, State"
            />
            {errors.location && (
              <p className="text-xs text-destructive mt-1">{errors.location.message}</p>
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
              <a href="#" className="text-primary underline-offset-4 hover:underline">
                terms and conditions
              </a>
            </label>
          </div>
          {errors.accept_terms && (
            <p className="text-xs text-destructive">{errors.accept_terms.message}</p>
          )}

          {/* Submit */}
          <button
            type="submit"
            disabled={isSubmitting}
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
