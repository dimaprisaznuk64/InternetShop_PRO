import { type InputHTMLAttributes, forwardRef } from "react";
import { Search, Eye, EyeOff } from "lucide-react";
import { useState } from "react";
import clsx from "clsx";
import "./Input.css";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  hint?: string;
  icon?: React.ReactNode;
  fullWidth?: boolean;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, hint, icon, fullWidth, className, type, ...props }, ref) => {
    const [showPassword, setShowPassword] = useState(false);
    const isPassword = type === "password";
    const resolvedType = isPassword && showPassword ? "text" : type;

    return (
      <div className={clsx("input-wrapper", fullWidth && "input-wrapper--full")}>
        {label && <label className="input-label">{label}</label>}
        <div className={clsx("input-container", error && "input-container--error")}>
          {icon && <span className="input-icon">{icon}</span>}
          <input
            ref={ref}
            type={resolvedType}
            className={clsx("input", icon && "input--with-icon", className)}
            {...props}
          />
          {isPassword && (
            <button
              type="button"
              className="input-eye"
              onClick={() => setShowPassword(!showPassword)}
              tabIndex={-1}
            >
              {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
            </button>
          )}
        </div>
        {error && <p className="input-error">{error}</p>}
        {hint && !error && <p className="input-hint">{hint}</p>}
      </div>
    );
  }
);

Input.displayName = "Input";

interface SearchInputProps extends Omit<InputProps, "icon" | "type"> {
  onSearch?: (value: string) => void;
}

export function SearchInput({ className, ...props }: SearchInputProps) {
  return (
    <Input
      type="search"
      icon={<Search size={16} />}
      className={clsx("input--search", className)}
      placeholder={props.placeholder || "Пошук..."}
      {...props}
    />
  );
}
