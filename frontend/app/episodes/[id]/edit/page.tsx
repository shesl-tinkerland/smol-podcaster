"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { episodeApi } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Sidebar } from "@/components/sidebar";
import { ShowNotesItem } from "@/types";
import { ArrowLeft, Plus, Trash2 } from "lucide-react";

export default function EditEpisodePage() {
  const params = useParams();
  const router = useRouter();
  const queryClient = useQueryClient();
  const episodeId = params.id as string;

  const [showNotes, setShowNotes] = useState<ShowNotesItem[]>([]);

  const { data: episode } = useQuery({
    queryKey: ["episode", episodeId],
    queryFn: () => episodeApi.get(episodeId),
    enabled: !!episodeId,
  });

  // Initialize show notes when episode data is loaded
  useState(() => {
    if (episode?.show_notes) {
      setShowNotes(episode.show_notes);
    }
  });

  const updateShowNotesMutation = useMutation({
    mutationFn: (items: ShowNotesItem[]) =>
      episodeApi.updateShowNotes(episodeId, items),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["episode", episodeId] });
      router.push("/episodes");
    },
  });

  const handleAddItem = () => {
    setShowNotes([...showNotes, { text: "", url: "" }]);
  };

  const handleRemoveItem = (index: number) => {
    setShowNotes(showNotes.filter((_, i) => i !== index));
  };

  const handleUpdateItem = (index: number, field: keyof ShowNotesItem, value: string) => {
    const updated = [...showNotes];
    updated[index] = { ...updated[index], [field]: value };
    setShowNotes(updated);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const validItems = showNotes.filter(item => item.text.trim() !== "");
    updateShowNotesMutation.mutate(validItems);
  };

  if (!episode) {
    return (
      <div className="flex h-screen bg-background">
        <Sidebar />
        <main className="flex-1 p-8">
          <div>Loading...</div>
        </main>
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-background">
      <Sidebar />
      <main className="flex-1 p-8 overflow-y-auto">
        <div className="max-w-4xl">
          <Button
            variant="ghost"
            onClick={() => router.push("/episodes")}
            className="mb-4"
          >
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Episodes
          </Button>

          <h2 className="text-3xl font-bold mb-6">Edit Show Notes: {episode.name}</h2>

          <Card>
            <CardHeader>
              <CardTitle>Show Notes</CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-4">
                {showNotes.map((item, index) => (
                  <div key={index} className="flex gap-2">
                    <Input
                      placeholder="Item text"
                      value={item.text}
                      onChange={(e) => handleUpdateItem(index, "text", e.target.value)}
                      className="flex-1"
                    />
                    <Input
                      placeholder="URL (optional)"
                      value={item.url || ""}
                      onChange={(e) => handleUpdateItem(index, "url", e.target.value)}
                      className="flex-1"
                    />
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      onClick={() => handleRemoveItem(index)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                ))}

                <Button
                  type="button"
                  variant="outline"
                  onClick={handleAddItem}
                  className="w-full"
                >
                  <Plus className="mr-2 h-4 w-4" />
                  Add Item
                </Button>

                <div className="flex gap-2 pt-4">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => router.push("/episodes")}
                    className="flex-1"
                  >
                    Cancel
                  </Button>
                  <Button
                    type="submit"
                    className="flex-1"
                    disabled={updateShowNotesMutation.isPending}
                  >
                    {updateShowNotesMutation.isPending ? "Saving..." : "Save Changes"}
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
}