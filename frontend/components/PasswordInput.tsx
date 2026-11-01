"use client";
import { useState } from "react";
import { Eye, EyeOff } from "lucide-react";
export function PasswordInput({ label = "password", ...props }: Omit<React.InputHTMLAttributes<HTMLInputElement>, "type"> & { label?: string }) {
  const [visible, setVisible] = useState(false);
  return <div className="password-field"><input {...props} aria-label={props["aria-label"] ?? (label === "password" ? "Password" : "Admin password")} type={visible ? "text" : "password"} /><button type="button" aria-label={`${visible ? "Hide" : "Show"} ${label}`} aria-pressed={visible} onClick={() => setVisible(!visible)}>{visible ? <EyeOff size={18} /> : <Eye size={18} />}</button></div>;
}
