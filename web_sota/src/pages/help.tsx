import { Book, Code, Info } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function Help() {
  return (
    <div className="space-y-6" data-testid="help-page">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white">
            Help & Documentation
          </h2>
          <p className="text-slate-300">
            Guidelines, standards, and usage patterns
          </p>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card className="border-slate-800 bg-slate-950/50">
          <CardHeader>
            <div className="flex items-center gap-2">
              <Book className="h-5 w-5 text-emerald-500" />
              <CardTitle className="text-white">Getting Started</CardTitle>
            </div>
          </CardHeader>
          <CardContent className="text-sm text-slate-300 space-y-4">
            <p>
              This MCP server provides a standardized interface for Microsoft
              OneNote operations via the Microsoft Graph API.
            </p>
            <p>Key concepts:</p>
            <ul className="list-disc list-inside space-y-1">
              <li>OAuth2 device-code authorization flows</li>
              <li>Notebook/Section/Page graph traversal</li>
              <li>FastMCP 3.4+ dual-transport bridge (stdio + HTTP)</li>
            </ul>
          </CardContent>
        </Card>

        <Card className="border-slate-800 bg-slate-950/50">
          <CardHeader>
            <div className="flex items-center gap-2">
              <Code className="h-5 w-5 text-blue-500" />
              <CardTitle className="text-white">Developer Standards</CardTitle>
            </div>
          </CardHeader>
          <CardContent className="text-sm text-slate-300 space-y-4">
            <p>
              Follow the fleet standards in mcp-central-docs/standards for all
              modifications. Tools use verb-led snake_case names with
              Annotated+Field parameters and SOTA docstrings.
            </p>
            <div className="p-3 bg-slate-900 rounded border border-slate-800 font-mono text-xs">
              <p># Ports (registered in WEBAPP_PORTS.md)</p>
              <p>BACKEND_PORT = 10907</p>
              <p>FRONTEND_PORT = 10906</p>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card className="border-slate-800 bg-slate-950/50">
        <CardHeader>
          <div className="flex items-center gap-2">
            <Info className="h-5 w-5 text-purple-500" />
            <CardTitle className="text-white">System Information</CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          <table className="w-full text-sm text-left text-slate-300">
            <tbody className="divide-y divide-slate-800">
              <tr>
                <td className="py-2 font-medium text-slate-200">
                  FastMCP Version
                </td>
                <td className="py-2 font-mono">3.4.4+</td>
              </tr>
              <tr>
                <td className="py-2 font-medium text-slate-200">Transport</td>
                <td className="py-2">stdio + HTTP streamable (/mcp)</td>
              </tr>
              <tr>
                <td className="py-2 font-medium text-slate-200">Backend API</td>
                <td className="py-2">http://127.0.0.1:10907/api/*</td>
              </tr>
            </tbody>
          </table>
        </CardContent>
      </Card>
    </div>
  );
}
