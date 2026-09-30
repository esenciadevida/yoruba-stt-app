import { Loader2 } from "lucide-react";

export default function ProfileLoading() {
  return (
    <div className="flex items-center justify-center py-32">
      <Loader2 className="w-8 h-8 animate-spin text-cyan-500" />
    </div>
  );
}
