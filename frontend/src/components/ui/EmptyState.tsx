import { Inbox, AlertTriangle } from "lucide-react";
import { Button } from "./Button";
import "./States.css";

interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description?: string;
  action?: { label: string; onClick: () => void };
}

export function EmptyState({ icon, title, description, action }: EmptyStateProps) {
  return (
    <div className="state state--empty">
      <div className="state__icon">{icon || <Inbox size={48} />}</div>
      <h3 className="state__title">{title}</h3>
      {description && <p className="state__desc">{description}</p>}
      {action && <Button onClick={action.onClick}>{action.label}</Button>}
    </div>
  );
}

interface ErrorStateProps {
  title?: string;
  message: string;
  onRetry?: () => void;
}

export function ErrorState({ title = "Щось пішло не так", message, onRetry }: ErrorStateProps) {
  return (
    <div className="state state--error">
      <div className="state__icon state__icon--error">
        <AlertTriangle size={48} />
      </div>
      <h3 className="state__title">{title}</h3>
      <p className="state__desc">{message}</p>
      {onRetry && (
        <Button variant="secondary" onClick={onRetry}>
          Повторити
        </Button>
      )}
    </div>
  );
}
