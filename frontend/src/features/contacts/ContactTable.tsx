import { Link } from "react-router-dom";

import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { formatDate, relativeFromNow } from "@/shared/lib/format";
import type { Contact } from "@/types/api";

export function ContactTable({ contacts }: { contacts: Contact[] }) {
  if (!contacts.length) {
    return (
      <EmptyState
        title="По этим фильтрам ничего не найдено"
        description="Измените условия поиска или добавьте новый контакт."
      />
    );
  }

  return (
    <Card className="min-w-0 overflow-hidden p-0">
      <div className="overflow-x-auto">
        <table className="w-full min-w-[860px] text-sm">
          <thead className="bg-white/5 text-left text-slate-400">
            <tr>
              <th className="px-5 py-4 font-medium">Контакт</th>
              <th className="px-5 py-4 font-medium">Категория</th>
              <th className="px-5 py-4 font-medium">Компания</th>
              <th className="px-5 py-4 font-medium">Последнее взаимодействие</th>
              <th className="px-5 py-4 font-medium">Теги</th>
            </tr>
          </thead>
          <tbody>
            {contacts.map((contact) => (
              <tr key={contact.id} className="border-t border-white/5 text-slate-300">
                <td className="px-5 py-4 align-top">
                  <Link to={`/contacts/${contact.id}`} className="block hover:text-white">
                    <p className="font-semibold text-white">
                      {contact.first_name} {contact.last_name ?? ""}
                    </p>
                    <p className="mt-1 text-xs uppercase tracking-[0.18em] text-slate-500">
                      Добавлен {formatDate(contact.created_at)}
                    </p>
                  </Link>
                </td>
                <td className="px-5 py-4 align-top">
                  {contact.category ? (
                    <Badge style={{ borderColor: `${contact.category.color}60`, color: contact.category.color }}>
                      {contact.category.name}
                    </Badge>
                  ) : (
                    "Без категории"
                  )}
                </td>
                <td className="px-5 py-4 align-top">{contact.company || contact.role || "Без компании"}</td>
                <td className="px-5 py-4 align-top">
                  <p>{relativeFromNow(contact.last_interaction_date)}</p>
                  <p className="mt-1 text-xs text-slate-500">{formatDate(contact.last_interaction_date)}</p>
                </td>
                <td className="px-5 py-4 align-top">
                  <div className="flex flex-wrap gap-2">
                    {contact.tags.slice(0, 3).map((tag) => (
                      <Badge key={tag.id}>{tag.name}</Badge>
                    ))}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
}
