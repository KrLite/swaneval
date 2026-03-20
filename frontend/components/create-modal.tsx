"use client";

import * as React from "react";
import { Card, CardContent } from "@/components/ui/card";

interface CreateModalProps {
  open: boolean;
  position: { top: number; right: number } | null;
  formDirty: boolean;
  onClose: () => void;
  onShake: () => void;
  title: string;
  children: React.ReactNode;
}

export function CreateModal({
  open,
  position,
  formDirty,
  onClose,
  onShake,
  title,
  children,
}: CreateModalProps) {
  if (!open || !position) return null;

  return (
    <>
      <div
        className="fixed inset-0 bg-black/40 z-50 animate-backdrop-in"
        onClick={() => {
          if (formDirty) {
            onShake();
            return;
          }
          onClose();
        }}
      />
      <div
        className="fixed z-[60] animate-modal-expand"
        style={{
          top: position.top,
          right: position.right,
          transformOrigin: "top right",
        }}
      >
        <Card className="w-[33vw]">
          <div className="flex items-center justify-between px-5 pt-5 pb-3">
            <h3 className="text-sm font-semibold">{title}</h3>
          </div>
          <CardContent className="pt-0 max-h-[70vh] overflow-auto">
            {children}
          </CardContent>
        </Card>
      </div>
    </>
  );
}
