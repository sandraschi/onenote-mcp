# Per-repo fleet start config for onenote-mcp
# Edit ports/backend target here - start.ps1 is fleet-standard.
@{
    Name         = 'onenote-mcp'
    BackendPort  = 10907
    FrontendPort = 10906
    HealthPath   = '/health'
    WebRoot      = 'D:\Dev\repos\onenote-mcp\web_sota'
    Backend = @{
        Kind          = 'uvicorn'
        UvicornTarget = 'onenote_mcp.server:app'
        SyncExtras    = @('dev')
        Env           = @{ WEB_PORT = '10907' }
    }
    Frontend = @{
        Kind           = 'vite-npm'
        PackageManager = 'npm'
        PortEnvVar     = 'VITE_PORT'
        ApiTargetEnv   = 'VITE_API_TARGET'
    }
}
