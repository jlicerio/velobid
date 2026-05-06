import { useCallback, useRef, useState } from 'react'
import { useParams } from 'react-router-dom'
import { toast } from 'sonner'
import { useGenerateBid, getViewBidUrl, getDownloadBidUrl } from './hooks'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Loader2, FileText, Download } from 'lucide-react'
import type { GenerateBidResponse } from '@/types'

type BidPackage = 'all' | 'client' | 'internal'

interface BidGenerateDialogProps {
  trade: string
}

export function BidGenerateDialog({ trade }: BidGenerateDialogProps) {
  const { projectId } = useParams<{ projectId: string }>()
  const [open, setOpen] = useState(false)
  const [packageName, setPackageName] = useState<BidPackage>('all')
  const [region, setRegion] = useState('')
  const generate = useGenerateBid()
  const [result, setResult] = useState<GenerateBidResponse | null>(null)
  const closeRef = useRef<HTMLButtonElement>(null)

  const handleGenerate = useCallback(async () => {
    if (!projectId || !trade) return
    setResult(null)
    try {
      const res = await generate.mutateAsync({
        project_id: projectId,
        trade,
        package_name: packageName,
        region: region || undefined,
        validate: true,
      })
      setResult(res)
      toast.success(`Bid generated: ${res.generated_files.length} file(s)`)
    } catch {
      toast.error('Failed to generate bid')
    }
  }, [projectId, trade, packageName, region, generate])

  const handleClose = useCallback(() => {
    setOpen(false)
    setResult(null)
    setPackageName('all')
    setRegion('')
    generate.reset()
  }, [generate])

  return (
    <Dialog
      open={open}
      onOpenChange={(nowOpen) => {
        if (!nowOpen) handleClose()
        setOpen(nowOpen)
      }}
    >
      <DialogTrigger asChild>
        <Button variant="default">
          <FileText className="mr-2 h-4 w-4" />
          Generate Bid PDF
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Generate Bid PDF</DialogTitle>
          <DialogDescription>
            Create PDF bid documents for the {trade} trade.
          </DialogDescription>
        </DialogHeader>

        {/* Form */}
        {!result && (
          <div className="space-y-4 py-2">
            <div className="space-y-2">
              <Label>Package</Label>
              <Select
                value={packageName}
                onValueChange={(v) => setPackageName(v as BidPackage)}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All (Client + Internal)</SelectItem>
                  <SelectItem value="client">Client Package</SelectItem>
                  <SelectItem value="internal">Internal Package</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="region">Region (optional)</Label>
              <Input
                id="region"
                placeholder="e.g. North East"
                value={region}
                onChange={(e) => setRegion(e.target.value)}
              />
            </div>
          </div>
        )}

        {/* Result */}
        {result && (
          <div className="space-y-3 py-2 max-h-64 overflow-y-auto">
            <p className="text-sm text-muted-foreground">
              {result.generated_files.length} file{result.generated_files.length !== 1 ? 's' : ''} generated.
            </p>
            {result.generated_files.map((file) => (
              <div
                key={file.filename}
                className="flex items-center justify-between rounded border p-2 text-sm"
              >
                <span className="truncate font-medium">{file.filename}</span>
                <div className="flex gap-2 shrink-0">
                  <Button
                    variant="outline"
                    size="sm"
                    asChild
                  >
                    <a
                      href={getViewBidUrl(
                        projectId!,
                        trade,
                        file.path.split('/')[2] || 'all',
                        file.filename,
                      )}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      View
                    </a>
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    asChild
                  >
                    <a
                      href={getDownloadBidUrl(
                        projectId!,
                        trade,
                        file.path.split('/')[2] || 'all',
                        file.filename,
                      )}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      <Download className="h-3 w-3 mr-1" />
                      Download
                    </a>
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}

        <DialogFooter>
          {result ? (
            <Button onClick={handleClose} variant="outline">
              Close
            </Button>
          ) : (
            <>
              <Button onClick={handleClose} variant="outline" ref={closeRef}>
                Cancel
              </Button>
              <Button
                onClick={handleGenerate}
                disabled={generate.isPending}
              >
                {generate.isPending ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Generating...
                  </>
                ) : (
                  'Generate'
                )}
              </Button>
            </>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
