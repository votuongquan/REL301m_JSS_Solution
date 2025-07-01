import * as React from "react"

export interface InputProps
  extends React.InputHTMLAttributes<HTMLInputElement> {
  variant?: 'default' | 'error' | 'success'
}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className = "", type, variant = 'default', ...props }, ref) => {
    let variantClass = ""
    if (variant === "error") {
      variantClass = "border-destructive focus-visible:ring-destructive"
    } else if (variant === "success") {
      variantClass = "border-green-500 focus-visible:ring-green-500"
    }

    const baseClass =
      "flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"

    const inputClass = [baseClass, variantClass, className].filter(Boolean).join(" ")

    return (
      <input
        type={type}
        className={inputClass}
        ref={ref}
        {...props}
      />
    )
  }
)
Input.displayName = "Input"

export { Input }