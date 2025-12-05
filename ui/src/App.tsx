import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import "./App.css";
import "antd/dist/reset.css";
import {
  ConfigProvider,
  theme,
  Button,
  Input,
  message,
  Tag,
  Select,
} from "antd";
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  addEdge,
  useEdgesState,
  useNodesState,
  Handle,
  Position,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import type { Connection } from "@xyflow/react";
import type { ChangeEvent } from "react";

type NodeConfigSchema = Record<
  string,
  {
    type: string;
    required?: boolean;
    default?: any;
    description?: string;
    enum?: any[];
  }
>;

type NodeCatalogItem = {
  type: string;
  label: string;
  category: string;
  description?: string;
  ports?: string[];
  config_schema?: NodeConfigSchema;
  outputs?: Record<string, any>;
  icon_url?: string;
};

type AuthUser = {
  id: number;
  email: string;
  role?: string;
};

const VITE_API_BASE_URL = import.meta.env?.VITE_API_BASE_URL;
console.log("VITE_API_BASE_URL", VITE_API_BASE_URL);
const ReactFlowAny: any = ReactFlow as any;

const CustomNode = ({ data }: { data: any }) => {
  const ports: string[] = (data?.ports || []).map((x: any) => String(x));
  const status: string | undefined = data?.status;
  const bg =
    status === "error"
      ? "#fde2e2"
      : status === "visited"
        ? "#e8f7e8"
        : "#ffffff";
  const iconUrl: string | undefined = data?.icon_url;

  return (
    <div
      className="node-card"
      style={{
        padding: 8,
        border: "1px solid var(--border)",
        borderRadius: 6,
        background: bg,
        minWidth: 180,
      }}
    >
      <Handle type="target" id="target" position={Position.Top} />
      <Handle type="target" id="target-left" position={Position.Left} />
      <Handle type="target" id="target-bottom" position={Position.Bottom} />
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 8,
          fontWeight: 600,
          marginBottom: 4,
        }}
      >
        {iconUrl && (
          <img
            src={iconUrl}
            alt={String(data?.type || "icon")}
            width={18}
            height={18}
            style={{ display: "block", borderRadius: 3 }}
          />
        )}
        <span>{data?.label || data?.type}</span>
      </div>
      <div style={{ fontSize: 12, color: "#666" }}>{data?.type}</div>
      <div style={{ display: "flex", gap: 6, marginTop: 6, flexWrap: "wrap" }}>
        {ports?.map((p: string) => (
          <div
            key={p}
            style={{
              fontSize: 10,
              background: "#eef",
              border: "1px solid #99f",
              borderRadius: 4,
              padding: "2px 4px",
            }}
          >
            {p}
          </div>
        ))}
      </div>
      {ports?.map((p: string, idx: number) => (
        <Handle
          key={p}
          type="source"
          id={p}
          position={Position.Right}
          style={{ top: 40 + idx * 16 }}
        />
      ))}
    </div>
  );
};

const nodeTypes = { custom: CustomNode };

function App() {
  const [catalog, setCatalog] = useState<NodeCatalogItem[]>([]);
  const [loadingCatalog, setLoadingCatalog] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);

  const [currentUser, setCurrentUser] = useState<AuthUser | null>(null);
  const [authMode, setAuthMode] = useState<"login" | "signup">("login");
  const [authEmail, setAuthEmail] = useState<string>("");
  const [authPassword, setAuthPassword] = useState<string>("");
  const [authLoading, setAuthLoading] = useState(false);

  // Flow state
  const [nodes, setNodes, onNodesChange] = useNodesState<any>([] as any[]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<any>([] as any[]);
  const idCounter = useRef(1);

  // Side panels
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [logsById, setLogsById] = useState<Record<string, any>>({});
  const [flowName, setFlowName] = useState<string>("new_flow.json");
  const [availableFlows, setAvailableFlows] = useState<string[]>([]);
  const [loadingFlows, setLoadingFlows] = useState(false);

  // Top bar inputs
  const [initialStateText, setInitialStateText] = useState<string>(
    "{" +
    '\n  "payload": {\n    "customer_name": "Alice",\n   "message": "This is urgent, please help!",\n  "email": "alice@example.com",\n    "phone": "+15551230000"\n  }\n' +
    "}"
  );
  const [payloadText, setPayloadText] = useState<string>("{}");

  const selectedNode = useMemo(
    () => nodes.find((n: any) => n.id === selectedNodeId),
    [nodes, selectedNodeId]
  );

  useEffect(() => {
    try {
      const stored = window.localStorage.getItem("flow_user");
      if (stored) {
        const parsed = JSON.parse(stored);
        if (
          parsed &&
          typeof parsed.email === "string" &&
          typeof parsed.id === "number"
        ) {
          setCurrentUser(parsed);
        }
      }
    } catch { }
  }, []);

  // Fetch nodes catalog
  useEffect(() => {
    const fetchCatalog = async () => {
      try {
        setLoadingCatalog(true);
        const res = await fetch(`${VITE_API_BASE_URL}/nodes`);
        const data = await res.json();
        setCatalog(data.nodes || []);
        setApiError(null);
      } catch (e: any) {
        setApiError(String(e));
      } finally {
        setLoadingCatalog(false);
      }
    };
    fetchCatalog();
  }, []);

  // Fetch flows list
  const fetchFlowsList = useCallback(async () => {
    try {
      setLoadingFlows(true);
      const res = await fetch(`${VITE_API_BASE_URL}/flows`);
      const data = await res.json();
      setAvailableFlows(data.flows || []);
    } catch (e) {
      // ignore
    } finally {
      setLoadingFlows(false);
    }
  }, []);
  useEffect(() => {
    fetchFlowsList();
  }, [fetchFlowsList]);

  const handleAuthSubmit = async () => {
    if (!authEmail || !authPassword) {
      message.warning("Enter email and password");
      return;
    }
    try {
      setAuthLoading(true);
      const path = authMode === "signup" ? "/auth/signup" : "/auth/login";
      const res = await fetch(`${VITE_API_BASE_URL}${path}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: authEmail, password: authPassword }),
      });
      if (!res.ok) {
        const errText = await res.text();
        message.error(`Auth failed: ${res.status} ${errText}`);
        return;
      }
      const data = await res.json();
      const user: AuthUser = {
        id: data.id,
        email: data.email,
        role: data.role,
      };
      setCurrentUser(user);
      window.localStorage.setItem("flowart_user", JSON.stringify(user));
      message.success(
        authMode === "signup" ? "Signup successful" : "Login successful"
      );
    } catch (e: any) {
      message.error(String(e));
    } finally {
      setAuthLoading(false);
    }
  };

  const handleLogout = () => {
    setCurrentUser(null);
    window.localStorage.removeItem("flowart_user");
  };

  // DnD handlers
  const onDragStart = (event: React.DragEvent, item: NodeCatalogItem) => {
    event.dataTransfer.setData("application/reactflow", JSON.stringify(item));
    event.dataTransfer.effectAllowed = "move";
  };

  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = "move";
  }, []);

  const deriveDefaultConfig = (item: NodeCatalogItem) => {
    const cfg: Record<string, any> = {};
    const schema = item.config_schema || {};
    Object.keys(schema).forEach((k) => {
      const s = schema[k];
      if (s?.default !== undefined) cfg[k] = s.default;
      else if (s?.type === "string") cfg[k] = "";
      else cfg[k] = "";
    });
    return cfg;
  };

  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();
      const raw = event.dataTransfer.getData("application/reactflow");
      if (!raw) return;
      const item: NodeCatalogItem = JSON.parse(raw);
      const rect = (event.target as HTMLElement).getBoundingClientRect();
      const position = {
        x: event.clientX - rect.left - 100,
        y: event.clientY - rect.top - 40,
      };
      const id = `${item.type.split(".").pop()}_${idCounter.current++}`;
      const newNode: any = {
        id,
        type: "custom",
        position,
        data: {
          type: item.type,
          label: item.label,
          ports: item.ports || [],
          icon_url: item.icon_url,
          config: deriveDefaultConfig(item),
        },
      };
      setNodes((nds) => nds.concat(newNode));
    },
    [setNodes]
  );

  const onConnect = useCallback(
    (connection: Connection) => {
      setEdges((eds) => addEdge({ ...connection, type: "smoothstep" }, eds));
    },
    [setEdges]
  );

  const onNodeClick = useCallback((_e: any, node: any) => {
    setSelectedNodeId(node.id);
  }, []);

  const updateSelectedNodeConfig = (updater: (cfg: any) => any) => {
    if (!selectedNodeId) return;
    setNodes((nds) =>
      nds.map((n: any) => {
        if (n.id !== selectedNodeId) return n;
        return {
          ...n,
          data: { ...n.data, config: updater(n.data.config || {}) },
        };
      })
    );
  };

  const applyRunResult = (trace: string[], logs: any[]) => {
    const visited = new Set(trace || []);
    const map: Record<string, any> = {};
    for (const l of logs || []) {
      if (l && l.id) map[l.id] = l;
    }
    setLogsById(map);
    setNodes((nds) =>
      nds.map((n: any) => {
        const log = map[n.id];
        let status: string | undefined = undefined;
        if (log?.status === "error") status = "error";
        else if (visited.has(n.id)) status = "visited";
        return { ...n, data: { ...n.data, status } };
      })
    );
  };

  const buildWorkflowJson = () => {
    const wfNodes = nodes.map((n: any) => ({
      id: n.id,
      type: n.data.type,
      config: n.data.config || {},
    }));
    const wfEdges = edges.map((e: any) => ({
      source: e.source,
      target: e.target,
      source_port: e.sourceHandle,
    }));

    // choose entry: prefer first trigger, else first with in-degree 0, else first node
    const firstTrigger = nodes.find((n: any) =>
      String(n.data.type).startsWith("trigger.")
    );
    let entry = firstTrigger?.id;
    if (!entry && nodes.length > 0) {
      const indeg: Record<string, number> = {};
      nodes.forEach((n: any) => (indeg[n.id] = 0));
      wfEdges.forEach(
        (e: any) => (indeg[e.target] = (indeg[e.target] || 0) + 1)
      );
      const zero = Object.keys(indeg).find((k) => indeg[k] === 0);
      entry = zero || nodes[0].id;
    }

    return { nodes: wfNodes, edges: wfEdges, entry };
  };

  const applyLoadedWorkflow = (wf: any) => {
    const wfNodes: any[] = Array.isArray(wf?.nodes) ? wf.nodes : [];
    const wfEdges: any[] = Array.isArray(wf?.edges) ? wf.edges : [];
    const newNodes = wfNodes.map((n: any, idx: number) => {
      const cat = catalog.find((c) => c.type === n.type);
      const ports = cat?.ports || [];
      const label = cat?.label || n.type;
      const icon_url = (cat as any)?.icon_url;
      const position = {
        x: 80 + (idx % 3) * 260,
        y: 80 + Math.floor(idx / 3) * 180,
      };
      return {
        id: n.id,
        type: "custom",
        position,
        data: { type: n.type, label, ports, icon_url, config: n.config || {} },
      } as any;
    });
    const newEdges = wfEdges.map((e: any) => ({
      id: `${e.source}-${e.source_port || "default"}-${e.target}`,
      source: e.source,
      target: e.target,
      sourceHandle: e.source_port,
      type: "smoothstep",
    }));
    setNodes(newNodes);
    setEdges(newEdges as any);
    setSelectedNodeId(null);
    setLogsById({});
  };

  const onLoadFlow = async (nameOverride?: string) => {
    const nm = String(nameOverride ?? flowName ?? "").trim();
    if (!nm) {
      message.warning("Enter a flow name");
      return;
    }
    try {
      const res = await fetch(
        `${VITE_API_BASE_URL}/flows/${encodeURIComponent(nm)}`
      );
      if (!res.ok) {
        const err = await res.text();
        message.error(`Load failed: ${res.status} ${err}`);
        return;
      }
      const data = await res.json();
      setFlowName(data?.name || nm);
      applyLoadedWorkflow(data?.workflow || {});
      message.success("Flow loaded");
    } catch (e: any) {
      message.error(String(e));
    }
  };

  const onSaveFlow = async () => {
    const nm = String(flowName ?? "").trim();
    if (!nm) {
      message.warning("Enter a flow name");
      return;
    }
    try {
      const workflow = buildWorkflowJson();
      const userIdParam = currentUser?.email
        ? `&user_id=${encodeURIComponent(currentUser.id)}`
        : "";
      const res = await fetch(
        `${VITE_API_BASE_URL}/flows/${encodeURIComponent(
          nm
        )}?overwrite=true${userIdParam}`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ workflow }),
        }
      );
      if (!res.ok) {
        const err = await res.text();
        message.error(`Save failed: ${res.status} ${err}`);
        return;
      }
      const out = await res.json();
      setFlowName(out?.name || nm);
      message.success("Flow saved");
      fetchFlowsList();
    } catch (e: any) {
      message.error(String(e));
    }
  };

  const runWorkflow = async () => {
    try {
      const workflow = buildWorkflowJson();
      const initial_state = JSON.parse(initialStateText || "{}");
      const payload = JSON.parse(payloadText || "{}");
      const res = await fetch(`${VITE_API_BASE_URL}/run-flow`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ workflow, initial_state, payload }),
      });
      if (!res.ok) {
        const errText = await res.text();
        message.error(`Run failed: ${res.status} ${errText}`);
        return;
      }
      const out = await res.json();
      const trace: string[] = out.trace || [];
      const logs: any[] = out.logs || [];
      applyRunResult(trace, logs);
      message.success("Workflow executed");
    } catch (e: any) {
      message.error(String(e));
    }
  };

  if (!currentUser) {
    return (
      <ConfigProvider theme={{ algorithm: theme.defaultAlgorithm }}>
        <div
          className="app-shell"
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <div
            style={{
              maxWidth: 360,
              width: "100%",
              padding: 24,
              borderRadius: 8,
              border: "1px solid var(--border)",
              background: "#ffffff",
              boxShadow: "0 8px 24px rgba(0,0,0,0.06)",
            }}
          >
            <h2 style={{ marginBottom: 16 }}>FlowArt</h2>
            <div style={{ marginBottom: 16, display: "flex", gap: 8 }}>
              <Button
                type={authMode === "login" ? "primary" : "default"}
                onClick={() => setAuthMode("login")}
                block
              >
                Login
              </Button>
              <Button
                type={authMode === "signup" ? "primary" : "default"}
                onClick={() => setAuthMode("signup")}
                block
              >
                Sign up
              </Button>
            </div>
            <div style={{ marginBottom: 12 }}>
              <div className="topbar-label">Email</div>
              <Input
                value={authEmail}
                onChange={(e: ChangeEvent<HTMLInputElement>) =>
                  setAuthEmail(e.target.value)
                }
                placeholder="you@example.com"
              />
            </div>
            <div style={{ marginBottom: 16 }}>
              <div className="topbar-label">Password</div>
              <Input.Password
                value={authPassword}
                onChange={(e: ChangeEvent<HTMLInputElement>) =>
                  setAuthPassword(e.target.value)
                }
                placeholder="Password"
              />
            </div>
            <Button
              type="primary"
              block
              loading={authLoading}
              onClick={handleAuthSubmit}
            >
              {authMode === "signup" ? "Create account" : "Login"}
            </Button>
            <div style={{ marginTop: 12, fontSize: 12 }}>
              Default user: <Tag>test@gmail.com / 123456789</Tag>
            </div>
          </div>
        </div>
      </ConfigProvider>
    );
  }

  return (
    <ConfigProvider theme={{ algorithm: theme.defaultAlgorithm }}>
      <div className="app-shell">
        <div className="topbar">

          <div className="topbar-actions">
            <div style={{ fontSize: 12, marginBottom: 8 }}>
              Logged in as <strong>{currentUser.email}</strong>{" "}
              <Button size="small" onClick={handleLogout}>
                Logout
              </Button>
            </div>

            <div
              style={{
                marginTop: 8,
                display: "flex",
                gap: 6,
                alignItems: "center",
              }}
            >
              <Input
                size="small"
                placeholder="flow name"
                value={flowName}
                onChange={(e: ChangeEvent<HTMLInputElement>) =>
                  setFlowName(e.target.value)
                }
                style={{ width: 180 }}
              />
              <Button onClick={() => onLoadFlow()}>
                Load
              </Button>
              <Button onClick={onSaveFlow}>
                Save
              </Button>
              <Button type="primary" onClick={runWorkflow}>
                Run
              </Button>
            </div>
            <div style={{ marginTop: 6 }}>
              <span style={{ fontSize: 12, marginBottom: 8, color: "var(--muted)" }}>
                Select flow example be loaded:{" "}
              </span>
              <Select
                size="small"
                style={{ width: 180 }}
                placeholder="examples"
                loading={loadingFlows}
                options={availableFlows.map((f) => ({ label: f, value: f }))}
                onOpenChange={(open) => {
                  if (open) fetchFlowsList();
                }}
                onChange={(val: string) => {
                  setFlowName(String(val));
                  onLoadFlow(val);
                }}
                value={undefined}
              />
            </div>
          </div>
        </div>

        <div className="content">
          <div className="sidebar left" onDragOver={onDragOver}>
            <div style={{ padding: 10 }}>
              <div className="sidebar-title">Initial State (JSON)</div>
              <Input.TextArea
                value={initialStateText}
                onChange={(e: ChangeEvent<HTMLTextAreaElement>) =>
                  setInitialStateText(e.target.value)
                }
                spellCheck={false}
                autoSize={{ minRows: 4, maxRows: 12 }}
              />
            </div>
            <div className="sidebar-title" style={{ marginTop: 20, padding: 10, borderTop: "1px solid #ddd" }}>Nodes</div>
            {loadingCatalog && <div className="muted">Loading...</div>}
            {apiError && <div className="error">{apiError}</div>}
            <div className="palette">
              {catalog.map((item) => (
                <div
                  key={item.type}
                  className="palette-item"
                  draggable
                  onDragStart={(e) => onDragStart(e, item)}
                >
                  <div
                    style={{ display: "flex", alignItems: "center", gap: 8 }}
                  >
                    {item.icon_url && (
                      <img
                        src={item.icon_url}
                        alt={`${item.type} icon`}
                        width={18}
                        height={18}
                        style={{ display: "block", borderRadius: 3 }}
                      />
                    )}
                    <div className="pi-label">{item.label}</div>
                  </div>
                  <div className="pi-type">Type: {item.type}</div>
                </div>
              ))}
            </div>

          </div>

          <div className="canvas" onDrop={onDrop} onDragOver={onDragOver}>
            <ReactFlowAny
              style={{ width: "100%", height: "100%" }}
              nodes={nodes as any}
              edges={edges as any}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              onConnect={onConnect}
              onNodeClick={onNodeClick}
              nodeTypes={nodeTypes}
              fitView
            >
              <Background />
              <MiniMap />
              <Controls />
            </ReactFlowAny>
          </div>

          <div className="sidebar right">
            <div className="sidebar-title">Selected Node</div>
            {!selectedNode && (
              <div className="muted">Click a node to edit config.</div>
            )}
            {selectedNode && (
              <div>
                <div className="kv">
                  <span>ID</span>
                  <span>{selectedNode.id}</span>
                </div>
                <div className="kv">
                  <span>Type</span>
                  <span>{(selectedNode as any).data?.type}</span>
                </div>
                {/* Last run result */}
                {logsById[selectedNode.id] && (
                  <div className="result-box">
                    <div className="config-label">Last Result</div>
                    <div
                      style={{
                        display: "flex",
                        gap: 8,
                        alignItems: "center",
                        marginBottom: 6,
                      }}
                    >
                      <Tag
                        color={
                          logsById[selectedNode.id].status === "error"
                            ? "red"
                            : "green"
                        }
                      >
                        {logsById[selectedNode.id].status || "unknown"}
                      </Tag>
                      {typeof logsById[selectedNode.id].port !==
                        "undefined" && (
                          <Tag>{String(logsById[selectedNode.id].port)}</Tag>
                        )}
                      {typeof logsById[selectedNode.id].elapsed_ms ===
                        "number" && (
                          <span className="muted">
                            {logsById[selectedNode.id].elapsed_ms} ms
                          </span>
                        )}
                    </div>
                    {logsById[selectedNode.id].status === "error" ? (
                      <pre className="pre-json">
                        {String(
                          logsById[selectedNode.id].error || "Unknown error"
                        )}
                      </pre>
                    ) : (
                      <pre className="pre-json">
                        {JSON.stringify(
                          logsById[selectedNode.id].outputs ?? {},
                          null,
                          2
                        )}
                      </pre>
                    )}
                  </div>
                )}
                <div className="config-editor">
                  <div className="config-label">Config (JSON)</div>
                  <Input.TextArea
                    value={JSON.stringify(
                      (selectedNode as any).data?.config || {},
                      null,
                      2
                    )}
                    onChange={(e: ChangeEvent<HTMLTextAreaElement>) => {
                      try {
                        const next = JSON.parse(e.target.value);
                        updateSelectedNodeConfig(() => next);
                      } catch (_) {
                        // ignore parse errors while typing
                      }
                    }}
                    spellCheck={false}
                    autoSize={{ minRows: 12 }}
                  />
                </div>
                <div style={{ marginTop: 12 }}>
                  <div className="config-label">Output format</div>
                  <pre className="pre-json">
                    {JSON.stringify(
                      (
                        catalog.find(
                          (c) => c.type === (selectedNode as any).data?.type
                        ) as any
                      )?.outputs || {},
                      null,
                      2
                    )}
                  </pre>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </ConfigProvider>
  );
}

export default App;
