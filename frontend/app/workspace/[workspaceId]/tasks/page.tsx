import { ListTodo } from "lucide-react";
import PlaceholderSection from "@/features/workspace/PlaceholderSection";

export default function TasksPage() {
  return (
    <PlaceholderSection
      icon={ListTodo}
      title="Tasks"
      comingIn="Task management coming in Sprint 2"
    />
  );
}
