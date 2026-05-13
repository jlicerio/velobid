import { Link } from "react-router-dom"
import { ArrowLeft } from "lucide-react"

export function PrivacyPage() {
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

        <h1 className="text-2xl font-semibold mb-4">Privacy Policy</h1>
        <p className="text-sm text-muted-foreground mb-6">Last updated: May 2026</p>

        <div className="prose prose-sm dark:prose-invert max-w-none space-y-4 text-sm text-foreground/80">
          <h2 className="text-lg font-medium text-foreground">1. Information We Collect</h2>
          <p>
            We collect information you provide directly, including your name, email
            address, company name, phone number, and location data when you create
            an account or use the Service.
          </p>

          <h2 className="text-lg font-medium text-foreground">2. How We Use Your Information</h2>
          <p>
            We use the information we collect to provide, maintain, and improve the
            Service, to communicate with you, and to comply with legal obligations.
          </p>

          <h2 className="text-lg font-medium text-foreground">3. Data Security</h2>
          <p>
            We implement industry-standard security measures to protect your data.
            However, no method of transmission or storage is 100% secure, and we
            cannot guarantee absolute security.
          </p>

          <h2 className="text-lg font-medium text-foreground">4. Data Sharing</h2>
          <p>
            We do not sell your personal information. We may share data with
            third-party service providers who assist in operating the Service, and
            as required by law.
          </p>

          <h2 className="text-lg font-medium text-foreground">5. Data Retention</h2>
          <p>
            We retain your information for as long as your account is active or as
            needed to provide the Service. You may request deletion of your data
            by contacting us.
          </p>

          <h2 className="text-lg font-medium text-foreground">6. Your Rights</h2>
          <p>
            Depending on your jurisdiction, you may have rights to access, correct,
            or delete your personal data, and to restrict or object to certain
            processing activities.
          </p>

          <h2 className="text-lg font-medium text-foreground">7. Cookies</h2>
          <p>
            We use essential cookies for authentication and session management. We
            do not use tracking cookies for advertising purposes.
          </p>

          <h2 className="text-lg font-medium text-foreground">8. Contact</h2>
          <p>
            For privacy-related inquiries, please contact privacy@velobid.com.
          </p>
        </div>
      </div>
    </div>
  )
}
