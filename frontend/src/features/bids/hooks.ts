import { useQuery, useMutation } from '@tanstack/react-query'
import { apiFetch } from '@/lib/api'
import type {
  BidPreviewResponse,
  GenerateBidRequest,
  GenerateBidResponse,
  ConfigSummary,
  VersionListResponse,
  VersionDetailResponse,
  VersionDiffResponse,
  CreateVersionRequest,
  CreateVersionResponse,
  RestoreVersionResponse,
} from '@/types'
import { queryClient } from '@/lib/api'

/* ---- Preview ---- */
export function useBidPreview(request: GenerateBidRequest | null) {
  return useQuery({
    queryKey: ['bid-preview', request?.project_id, request?.trade, request?.region],
    queryFn: () =>
      apiFetch<BidPreviewResponse>('/bids/preview', {
        method: 'POST',
        body: request,
      }),
    enabled: !!request?.project_id && !!request?.trade,
  })
}

/* ---- Generate ---- */
export function useGenerateBid() {
  return useMutation({
    mutationFn: (request: GenerateBidRequest) =>
      apiFetch<GenerateBidResponse>('/bids/generate', {
        method: 'POST',
        body: request,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bid-versions'] })
    },
  })
}

/* ---- Trades ---- */
export function useTrades() {
  return useQuery({
    queryKey: ['trades'],
    queryFn: () => apiFetch<ConfigSummary[]>('/trades'),
  })
}

/* ---- Versions ---- */
export function useVersionsList(projectId: string, trade: string) {
  return useQuery({
    queryKey: ['bid-versions', projectId, trade],
    queryFn: () =>
      apiFetch<VersionListResponse>(
        `/bids/${projectId}/${trade}/versions`,
      ),
    enabled: !!projectId && !!trade,
  })
}

export function useVersionDetail(projectId: string, trade: string, versionId: string | null) {
  return useQuery({
    queryKey: ['bid-version', projectId, trade, versionId],
    queryFn: () =>
      apiFetch<VersionDetailResponse>(
        `/bids/${projectId}/${trade}/versions/${versionId}`,
      ),
    enabled: !!projectId && !!trade && !!versionId,
  })
}

export function useVersionDiff(projectId: string, trade: string, versionId: string | null) {
  return useQuery({
    queryKey: ['bid-version-diff', projectId, trade, versionId],
    queryFn: () =>
      apiFetch<VersionDiffResponse>(
        `/bids/${projectId}/${trade}/versions/${versionId}/diff`,
      ),
    enabled: !!projectId && !!trade && !!versionId,
  })
}

export function useCreateVersion(projectId: string, trade: string) {
  return useMutation({
    mutationFn: (request: CreateVersionRequest) =>
      apiFetch<CreateVersionResponse>(
        `/bids/${projectId}/${trade}/versions`,
        { method: 'POST', body: request },
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bid-versions', projectId, trade] })
    },
  })
}

export function useRestoreVersion(projectId: string, trade: string) {
  return useMutation({
    mutationFn: (versionId: string) =>
      apiFetch<RestoreVersionResponse>(
        `/bids/${projectId}/${trade}/versions/${versionId}/restore`,
        { method: 'POST' },
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bid-versions', projectId, trade] })
      queryClient.invalidateQueries({ queryKey: ['bid-preview'] })
    },
  })
}

/* ---- View / Download URLs ---- */
export function getViewBidUrl(
  projectId: string,
  trade: string,
  pkg: string,
  filename: string,
): string {
  return `/api/v1/bids/${projectId}/${trade}/${pkg}/view/${filename}`
}

export function getDownloadBidUrl(
  projectId: string,
  trade: string,
  pkg: string,
  filename: string,
): string {
  return `/api/v1/bids/${projectId}/${trade}/${pkg}/download/${filename}`
}

/* ---- Formatting helpers ---- */
export function formatCurrency(value: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
  }).format(value)
}

export function formatNumber(value: number, decimals = 2): string {
  return value.toLocaleString('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  })
}
