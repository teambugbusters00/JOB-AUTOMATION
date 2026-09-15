import * as React from "react";
import { cn } from "@/lib/utils";

type Props = React.ButtonHTMLAttributes<HTMLButtonElement> & {variant?:"default"|"outline"|"ghost"; size?:"sm"|"default"};
export function Button({className,variant="default",size="default",...props}:Props){return <button className={cn("ui-button",variant==="outline"&&"ui-outline",variant==="ghost"&&"ui-ghost",size==="sm"&&"ui-sm",className)} {...props}/>}
