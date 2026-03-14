import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface Props {
  notification: {
    id: string;
    type: string;
    title: string;
    body: string;
    read: boolean;
    createdAt: string | Date;
  };
  onMarkRead: (id: string) => void;
}

export function NotificationItem({ notification, onMarkRead }: Props) {
  return (
    <Card className={notification.read ? "opacity-60" : ""}>
      <CardContent className="p-4">
        <div className="flex items-start justify-between">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-semibold">{notification.title}</h3>
              {!notification.read && (
                <Badge className="bg-indigo-600 text-xs">New</Badge>
              )}
            </div>
            <p className="text-sm text-muted-foreground">{notification.body}</p>
            <p className="text-xs text-muted-foreground">
              {new Date(notification.createdAt).toLocaleString()}
            </p>
          </div>
          {!notification.read && (
            <button
              onClick={() => onMarkRead(notification.id)}
              className="text-xs text-indigo-600 hover:underline"
            >
              Mark read
            </button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
