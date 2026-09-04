import { Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import Dashboard from "./pages/Dashboard";
import Payments from "./pages/Payments";
import Receivables from "./pages/Receivables";
import BatchRunner from "./pages/BatchRunner";
import AuditTrail from "./pages/AuditTrail";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/payments" element={<Payments />} />
        <Route path="/receivables" element={<Receivables />} />
        <Route path="/batches" element={<BatchRunner />} />
        <Route path="/audit" element={<AuditTrail />} />
      </Route>
    </Routes>
  );
}
