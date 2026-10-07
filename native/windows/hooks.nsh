; Installer hooks for onenote-mcp (Tauri NSIS).
; "Register in AI tools" page + register/unregister come from the vendored fleet include
; mcp-clients.nsh (copied from mcp-central-docs by native/build.ps1 - do not edit it here).
!define MCP_REG_NAME "onenote-mcp"
!define MCP_REG_EXE "onenote-mcp-backend.exe"
!include "${__FILEDIR__}\mcp-clients.nsh"

; Kill UI + backend before install/uninstall (backend locks resources/*.exe).
!macro KillOnenoteMcpFleetProcesses
  DetailPrint "Stopping onenote-mcp processes..."
  ExecWait 'taskkill /F /IM onenote-mcp-backend.exe /T' $0
  ExecWait 'taskkill /F /IM onenote-mcp-native.exe /T' $0
  !if "${INSTALLMODE}" == "currentUser"
    nsis_tauri_utils::KillProcessCurrentUser "onenote-mcp-backend.exe"
    Pop $0
    nsis_tauri_utils::KillProcessCurrentUser "onenote-mcp-native.exe"
    Pop $0
  !else
    nsis_tauri_utils::KillProcess "onenote-mcp-backend.exe"
    Pop $0
    nsis_tauri_utils::KillProcess "onenote-mcp-native.exe"
    Pop $0
  !endif
  Sleep 2000
!macroend

!macro NSIS_HOOK_PREINSTALL
  !insertmacro KillOnenoteMcpFleetProcesses
!macroend

!macro NSIS_HOOK_PREUNINSTALL
  !insertmacro McpClientsUnregister
  !insertmacro KillOnenoteMcpFleetProcesses
!macroend

!macro NSIS_HOOK_POSTINSTALL
  !insertmacro McpClientsRegister
!macroend
