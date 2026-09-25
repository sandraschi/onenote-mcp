import {
  Navigate,
  Route,
  BrowserRouter as Router,
  Routes,
} from "react-router-dom";
import { useZoom } from "@/common/use-zoom";
import { AppLayout } from "@/components/layout/app-layout";
import { Apps } from "@/pages/apps";
import { Chat } from "@/pages/chat";
import { Dashboard } from "@/pages/dashboard";
import { Help } from "@/pages/help";
import Logging from "@/pages/Logging";
import { Notebooks } from "@/pages/notebooks";
import { SearchPage } from "@/pages/search";
import { Settings } from "@/pages/settings";
import { Skills } from "@/pages/skills";
import { Status } from "@/pages/status";
import { Tools } from "@/pages/tools";

function App() {
  useZoom();
  return (
    <Router>
      <AppLayout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/notebooks" element={<Notebooks />} />
          <Route path="/search" element={<SearchPage />} />
          <Route path="/tools" element={<Tools />} />
          <Route path="/status" element={<Status />} />
          <Route path="/apps" element={<Apps />} />
          <Route path="/chat" element={<Chat />} />
          <Route path="/logging" element={<Logging />} />
          <Route path="/skills" element={<Skills />} />
          <Route path="/help" element={<Help />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AppLayout>
    </Router>
  );
}

export default App;
