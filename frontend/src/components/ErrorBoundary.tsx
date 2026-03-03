/**
 * React Error Boundary — catches Three.js / WebGL crashes gracefully.
 * Shows a fallback UI instead of a white screen of death.
 */

import React from "react";

interface Props {
  children: React.ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export default class ErrorBoundary extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    console.error("[ErrorBoundary]", error, info.componentStack);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            height: "100%",
            background: "#1a1a2e",
            borderRadius: 12,
            color: "#f87171",
            padding: 32,
            textAlign: "center",
            gap: 12,
          }}
        >
          <div style={{ fontSize: 32 }}>⚠️</div>
          <div style={{ fontSize: 14, fontWeight: 600 }}>3D Viewport Error</div>
          <div style={{ fontSize: 12, color: "#888", maxWidth: 300 }}>
            {this.state.error?.message ?? "An unexpected error occurred in the 3D renderer."}
          </div>
          <button
            onClick={() => this.setState({ hasError: false, error: null })}
            style={{
              padding: "8px 16px",
              borderRadius: 6,
              border: "none",
              background: "#a78bfa",
              color: "#000",
              fontSize: 12,
              fontWeight: 600,
              cursor: "pointer",
              marginTop: 8,
            }}
          >
            Retry
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
