import { Link } from "react-router-dom"
import { ArrowLeft } from "lucide-react"

export function TermsPage() {
  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-2xl mx-auto px-4 py-8">
        <Link
          to="/signup"
          className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground mb-6"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to sign up
        </Link>

        <h1 className="text-2xl font-semibold mb-4">Terms and Conditions</h1>
        <p className="text-sm text-muted-foreground mb-6">Last updated: May 2026</p>

        <div className="prose prose-sm dark:prose-invert max-w-none space-y-4 text-sm text-foreground/80">
          <h2 className="text-lg font-medium text-foreground">1. Acceptance of Terms</h2>
          <p>
            By accessing or using VeloBid ("the Service"), you agree to be bound by these
            Terms and Conditions. If you do not agree, do not use the Service.
          </p>

          <h2 className="text-lg font-medium text-foreground">2. Description of Service</h2>
          <p>
            VeloBid provides a construction estimating platform that enables users to
            manage bids, projects, and related documentation. The Service is provided
            "as is" and we reserve the right to modify or discontinue it at any time.
          </p>

          <h2 className="text-lg font-medium text-foreground">3. User Accounts</h2>
          <p>
            You are responsible for maintaining the confidentiality of your account
            credentials and for all activities that occur under your account. You must
            notify us immediately of any unauthorized use.
          </p>

          <h2 className="text-lg font-medium text-foreground">4. Acceptable Use</h2>
          <p>
            You agree not to use the Service for any unlawful purpose or in violation
            of any applicable laws. You may not attempt to gain unauthorized access to
            any part of the Service.
          </p>

          <h2 className="text-lg font-medium text-foreground">5. Privacy</h2>
          <p>
            Your use of the Service is also governed by our{" "}
            <Link to="/privacy" className="text-primary underline">
              Privacy Policy
            </Link>
            .
          </p>

          <h2 className="text-lg font-medium text-foreground">6. Limitation of Liability</h2>
          <p>
            VeloBid shall not be liable for any indirect, incidental, special,
            consequential, or punitive damages arising from your use of the Service.
          </p>

          <h2 className="text-lg font-medium text-foreground">7. Changes to Terms</h2>
          <p>
            We reserve the right to update these terms at any time. Continued use of
            the Service after changes constitutes acceptance of the new terms.
          </p>

          <h2 className="text-lg font-medium text-foreground">8. Contact</h2>
          <p>
            For questions about these terms, please contact support@velobid.com.
          </p>
        </div>
      </div>
    </div>
  )
}
