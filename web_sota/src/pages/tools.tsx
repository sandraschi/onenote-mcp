import { BookOpen, Copy, Search, Wrench } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function Tools() {
  return (
    <div className="space-y-6" data-testid="tools-page">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white">
            Tool Inventory
          </h2>
          <p className="text-slate-300">
            Available portmanteau interfaces for OneNote Knowledge Management
          </p>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <Card className="border-slate-800 bg-slate-950/50">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-200">
              Notebook Explorer
            </CardTitle>
            <BookOpen className="h-4 w-4 text-emerald-500" />
          </CardHeader>
          <CardContent>
            <p className="text-xs text-slate-400">
              Browse notebooks, sections, and pages hierarchically
            </p>
          </CardContent>
        </Card>
        <Card className="border-slate-800 bg-slate-950/50">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-200">
              Global Search
            </CardTitle>
            <Search className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <p className="text-xs text-slate-400">
              Query your entire OneNote graph via Microsoft Graph API
            </p>
          </CardContent>
        </Card>
        <Card className="border-slate-800 bg-slate-950/50">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-200">
              Content Importer
            </CardTitle>
            <Copy className="h-4 w-4 text-purple-500" />
          </CardHeader>
          <CardContent>
            <p className="text-xs text-slate-400">
              Sync web clips and external documents to pages
            </p>
          </CardContent>
        </Card>
      </div>

      <Card className="border-slate-800 bg-slate-950/50">
        <CardHeader>
          <CardTitle className="text-white">Active Capabilities</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center justify-between p-3 rounded-lg bg-slate-900/50 border border-slate-800">
              <div className="flex items-center">
                <Wrench className="h-4 w-4 text-slate-400 mr-3" />
                <span className="text-sm font-medium text-slate-200">
                  onenote_sync
                </span>
              </div>
              <span className="text-xs text-emerald-500 font-mono">READY</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
