import * as React from "react"
import { Input, InputProps } from "./input"

interface InputWithIconProps extends InputProps {
  leftIcon?: React.ReactNode
  rightIcon?: React.ReactNode
  onRightIconClick?: () => void
  onLeftIconClick?: () => void
}

const InputWithIcon = React.forwardRef<HTMLInputElement, InputWithIconProps>(
  ({
    className,
    leftIcon,
    rightIcon,
    onLeftIconClick,
    onRightIconClick,
    ...props
  }, ref) => {
    // Compute input padding classes
    let inputClass = className || ""
    if (leftIcon) inputClass += (inputClass ? " " : "") + "pl-10"
    if (rightIcon) inputClass += (inputClass ? " " : "") + "pr-10"

    return (
      <div className="relative">
        {leftIcon && (
          <div
            className={
              "absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground" +
              (onLeftIconClick ? " cursor-pointer hover:text-foreground" : "")
            }
            onClick={onLeftIconClick}
          >
            {leftIcon}
          </div>
        )}

        <Input
          className={inputClass}
          ref={ref}
          {...props}
        />

        {rightIcon && (
          <div
            className={
              "absolute right-3 top-1/2 transform -translate-y-1/2 text-muted-foreground" +
              (onRightIconClick ? " cursor-pointer hover:text-foreground" : "")
            }
            onClick={onRightIconClick}
          >
            {rightIcon}
          </div>
        )}
      </div>
    )
  }
)

InputWithIcon.displayName = "InputWithIcon"

export { InputWithIcon }