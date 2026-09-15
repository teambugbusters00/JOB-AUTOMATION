"use client";

import { AnimatePresence, motion } from "motion/react";
import { cn } from "@/lib/utils";
import type { ReactNode } from "react";

export function AnimatedList({children,className}:{children:ReactNode;className?:string}){
  return <div className={cn("animated-list",className)}><AnimatePresence initial={false}>{children}</AnimatePresence></div>;
}

export function AnimatedListItem({children,index=0,className}:{children:ReactNode;index?:number;className?:string}){
  return <motion.div layout initial={{opacity:0,y:10,scale:.98}} animate={{opacity:1,y:0,scale:1}} exit={{opacity:0,y:-8}} transition={{duration:.28,delay:index*.04}} className={className}>{children}</motion.div>;
}
