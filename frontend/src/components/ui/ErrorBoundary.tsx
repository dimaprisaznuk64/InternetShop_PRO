import { Component } from "react";

interface Props {
  children: React.ReactNode;
}

interface State {
  hasError: boolean;
  message: string;
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, message: "" };

  static getDerivedStateFromError(error: unknown): State {
    return {
      hasError: true,
      message: error instanceof Error ? error.message : String(error),
    };
  }

  componentDidCatch(error: unknown) {
    console.error("App crashed:", error);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: "4rem 1rem", textAlign: "center" }}>
          <h1 style={{ marginBottom: "0.5rem" }}>Щось пішло не так</h1>
          <p style={{ color: "#888", marginBottom: "1.5rem" }}>
            {this.state.message}
          </p>
          <button
            onClick={() => window.location.assign("/")}
            style={{
              padding: "0.6rem 1.5rem",
              cursor: "pointer",
              borderRadius: 8,
              border: "1px solid currentColor",
              background: "transparent",
              fontSize: "1rem",
            }}
          >
            На головну
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
