import json
from datetime import date, datetime, timezone
from urllib.parse import urlparse

from odoo import fields, http
from odoo.http import request

from ..services.ai_agent import LightweightContactAgent


class NetworkPilotCollaborationAPI(http.Controller):
    def _json_response(self, data=None, status=200):
        body = "" if status == 204 else json.dumps(data, default=str, ensure_ascii=False)
        return request.make_response(
            body,
            headers=[("Content-Type", "application/json")],
            status=status,
        )

    def _json_payload(self):
        try:
            return json.loads(request.httprequest.data or b"{}")
        except Exception:
            return None

    def _bad_json(self):
        return self._json_response({"detail": "Invalid JSON"}, status=400)

    def _current_user_id(self):
        return request.env.user.id

    def _safe_int(self, value):
        if value in (None, "", False):
            return False
        try:
            return int(value)
        except (TypeError, ValueError):
            return False

    def _clean_text(self, value):
        if value in (None, ""):
            return False
        return str(value).strip()

    def _parse_datetime(self, value):
        if not value:
            return False
        if isinstance(value, datetime):
            return fields.Datetime.to_string(value)
        raw = str(value).strip().replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(raw)
        except ValueError:
            return False
        if parsed.tzinfo:
            parsed = parsed.astimezone(timezone.utc).replace(tzinfo=None)
        return fields.Datetime.to_string(parsed)

    def _is_same_origin(self):
        host_url = request.httprequest.host_url.rstrip("/")
        allowed = {host_url}
        origin = (request.httprequest.headers.get("Origin") or "").rstrip("/")
        referer = request.httprequest.headers.get("Referer") or ""
        if origin:
            return origin in allowed
        if referer:
            parsed = urlparse(referer)
            referer_origin = f"{parsed.scheme}://{parsed.netloc}".rstrip("/")
            return referer_origin in allowed
        return False

    def _forbid_cross_origin(self):
        if not self._is_same_origin():
            return self._json_response({"detail": "Cross-origin request denied"}, status=403)
        return None

    def _contact_domain(self):
        return [("user_id", "=", self._current_user_id())]

    def _get_contact(self, contact_id):
        return request.env["networkpilot.contact"].sudo().search(
            self._contact_domain() + [("id", "=", self._safe_int(contact_id))],
            limit=1,
        )

    def _contact_status(self, contact):
        return contact.network_status if contact.network_status else "target"

    def _status_color(self, status):
        return {
            "active": "#14b8a6",
            "target": "#f59e0b",
            "dormant": "#f43f5e",
            "self": "#f8fafc",
        }.get(status, "#94a3b8")

    def _contact_preview(self, contact):
        if not contact:
            return None
        return {
            "id": contact.id,
            "full_name": contact.full_name,
            "first_name": contact.first_name,
            "last_name": contact.last_name or None,
            "company": contact.company or None,
            "role": contact.role or None,
            "importance_level": contact.importance_level,
            "status": self._contact_status(contact),
        }

    def _relationship_payload(self, relationship):
        return {
            "id": relationship.id,
            "user_id": relationship.user_id.id,
            "source_contact": self._contact_preview(relationship.source_contact_id),
            "target_contact": self._contact_preview(relationship.target_contact_id),
            "relationship_type": relationship.relationship_type,
            "strength": relationship.strength,
            "shared_context": relationship.shared_context or None,
            "notes": relationship.notes or None,
            "last_active_at": relationship.last_active_at or None,
            "message_count": relationship.message_count,
            "interaction_count": relationship.interaction_count,
            "is_bridge": relationship.is_bridge,
            "pair_key": relationship.pair_key,
        }

    def _message_payload(self, message):
        return {
            "id": message.id,
            "pair_key": message.pair_key,
            "sender_contact": self._contact_preview(message.sender_contact_id),
            "recipient_contact": self._contact_preview(message.recipient_contact_id),
            "body": message.body,
            "message_type": message.message_type,
            "sent_at": message.sent_at,
            "metadata_json": json.loads(message.metadata_json or "{}"),
            "is_ai_draft": message.is_ai_draft,
        }

    def _relationship_from_pair(self, pair_key):
        return request.env["networkpilot.contact_relationship"].sudo().search(
            [
                ("user_id", "=", self._current_user_id()),
                ("pair_key", "=", pair_key),
            ],
            limit=1,
        )

    @http.route("/api/v1/network/relationships", type="http", auth="user", methods=["GET"], csrf=False)
    def list_relationships(self, **kwargs):
        relationships = request.env["networkpilot.contact_relationship"].sudo().search(
            [("user_id", "=", self._current_user_id())],
            order="strength desc, last_active_at desc, id desc",
        )
        return self._json_response([self._relationship_payload(item) for item in relationships])

    @http.route("/api/v1/network/relationships", type="http", auth="user", methods=["POST"], csrf=False)
    def create_relationship(self, **kwargs):
        forbidden = self._forbid_cross_origin()
        if forbidden:
            return forbidden
        data = self._json_payload()
        if data is None:
            return self._bad_json()
        source_contact = self._get_contact(data.get("source_contact_id"))
        target_contact = self._get_contact(data.get("target_contact_id"))
        if not source_contact or not target_contact:
            return self._json_response({"detail": "Both contacts must exist"}, status=404)
        try:
            relationship = request.env["networkpilot.contact_relationship"].sudo().create(
                {
                    "user_id": self._current_user_id(),
                    "source_contact_id": source_contact.id,
                    "target_contact_id": target_contact.id,
                    "relationship_type": data.get("relationship_type") or "professional",
                    "strength": float(data.get("strength") or 1.0),
                    "shared_context": self._clean_text(data.get("shared_context")),
                    "notes": self._clean_text(data.get("notes")),
                    "is_bridge": bool(data.get("is_bridge")),
                    "last_active_at": self._parse_datetime(data.get("last_active_at")) or fields.Datetime.now(),
                }
            )
        except Exception as exc:
            return self._json_response({"detail": str(exc)}, status=409)
        return self._json_response(self._relationship_payload(relationship), status=201)

    @http.route("/api/v1/network/relationships/<int:relationship_id>", type="http", auth="user", methods=["PATCH"], csrf=False)
    def update_relationship(self, relationship_id, **kwargs):
        forbidden = self._forbid_cross_origin()
        if forbidden:
            return forbidden
        relationship = request.env["networkpilot.contact_relationship"].sudo().search(
            [
                ("id", "=", relationship_id),
                ("user_id", "=", self._current_user_id()),
            ],
            limit=1,
        )
        if not relationship:
            return self._json_response({"detail": "Relationship not found"}, status=404)
        data = self._json_payload()
        if data is None:
            return self._bad_json()
        vals = {}
        for field_name in ("relationship_type", "shared_context", "notes"):
            if field_name in data:
                vals[field_name] = self._clean_text(data.get(field_name))
        if "strength" in data:
            vals["strength"] = float(data.get("strength") or 1.0)
        if "is_bridge" in data:
            vals["is_bridge"] = bool(data.get("is_bridge"))
        if "last_active_at" in data:
            vals["last_active_at"] = self._parse_datetime(data.get("last_active_at")) or fields.Datetime.now()
        if vals:
            relationship.write(vals)
        return self._json_response(self._relationship_payload(relationship))

    @http.route("/api/v1/network/relationships/<int:relationship_id>", type="http", auth="user", methods=["DELETE"], csrf=False)
    def delete_relationship(self, relationship_id, **kwargs):
        forbidden = self._forbid_cross_origin()
        if forbidden:
            return forbidden
        relationship = request.env["networkpilot.contact_relationship"].sudo().search(
            [
                ("id", "=", relationship_id),
                ("user_id", "=", self._current_user_id()),
            ],
            limit=1,
        )
        if not relationship:
            return self._json_response({"detail": "Relationship not found"}, status=404)
        relationship.unlink()
        return self._json_response(status=204)

    @http.route("/api/v1/network/graph", type="http", auth="user", methods=["GET"], csrf=False)
    def get_network_graph(self, **kwargs):
        contacts = request.env["networkpilot.contact"].sudo().search(self._contact_domain(), order="full_name asc")
        relationships = request.env["networkpilot.contact_relationship"].sudo().search(
            [("user_id", "=", self._current_user_id())],
            order="strength desc, last_active_at desc",
        )

        degree_map = {contact.id: 1 for contact in contacts}
        for relationship in relationships:
            degree_map[relationship.source_contact_id.id] = degree_map.get(relationship.source_contact_id.id, 1) + 1
            degree_map[relationship.target_contact_id.id] = degree_map.get(relationship.target_contact_id.id, 1) + 1

        nodes = [
            {
                "id": "user",
                "label": request.env.user.name or "You",
                "status": "self",
                "color": self._status_color("self"),
                "size": 22,
                "degree": len(contacts),
                "is_bridge": False,
            }
        ]
        active_count = 0
        target_count = 0
        dormant_count = 0
        bridge_contacts = []
        for contact in contacts:
            status = self._contact_status(contact)
            if status == "active":
                active_count += 1
            elif status == "target":
                target_count += 1
            else:
                dormant_count += 1
            is_bridge = degree_map.get(contact.id, 1) >= 4
            if is_bridge:
                bridge_contacts.append(contact.full_name)
            nodes.append(
                {
                    "id": contact.id,
                    "label": contact.full_name,
                    "status": status,
                    "color": self._status_color(status),
                    "size": 10 + min(degree_map.get(contact.id, 1) * 2, 16),
                    "degree": degree_map.get(contact.id, 1),
                    "importance_level": contact.importance_level,
                    "company": contact.company or None,
                    "category_name": contact.category_id.name if contact.category_id else None,
                    "is_bridge": is_bridge,
                }
            )

        links = []
        for contact in contacts:
            links.append(
                {
                    "source": "user",
                    "target": contact.id,
                    "weight": 2.5 if contact.importance_level in ("high", "strategic") else 1.5,
                    "kind": "user_contact",
                }
            )
        for relationship in relationships:
            links.append(
                {
                    "source": relationship.source_contact_id.id,
                    "target": relationship.target_contact_id.id,
                    "weight": max(1.0, min(relationship.strength + (relationship.message_count * 0.15), 5.0)),
                    "kind": relationship.relationship_type,
                    "pair_key": relationship.pair_key,
                }
            )

        summary = {
            "total_contacts": len(contacts),
            "total_relationships": len(relationships),
            "active_contacts": active_count,
            "target_contacts": target_count,
            "dormant_contacts": dormant_count,
            "bridge_contacts": len(set(bridge_contacts)),
            "bridge_names": sorted(set(bridge_contacts))[:5],
        }
        return self._json_response({"nodes": nodes, "links": links, "summary": summary})

    @http.route("/api/v1/messages/conversations", type="http", auth="user", methods=["GET"], csrf=False)
    def list_conversations(self, **kwargs):
        messages = request.env["networkpilot.contact_message"].sudo().search(
            [("user_id", "=", self._current_user_id())],
            order="sent_at desc, id desc",
        )
        seen = set()
        conversations = []
        for message in messages:
            if message.pair_key in seen:
                continue
            seen.add(message.pair_key)
            conversation_messages = messages.filtered(lambda item: item.pair_key == message.pair_key)
            relationship = self._relationship_from_pair(message.pair_key)
            participants = sorted(
                [
                    self._contact_preview(message.sender_contact_id),
                    self._contact_preview(message.recipient_contact_id),
                ],
                key=lambda item: item["id"],
            )
            conversations.append(
                {
                    "pair_key": message.pair_key,
                    "participants": participants,
                    "last_message": self._message_payload(message),
                    "message_count": len(conversation_messages),
                    "relationship": self._relationship_payload(relationship) if relationship else None,
                }
            )
        return self._json_response(conversations)

    @http.route("/api/v1/messages/conversations/<string:pair_key>", type="http", auth="user", methods=["GET"], csrf=False)
    def get_conversation(self, pair_key, **kwargs):
        messages = request.env["networkpilot.contact_message"].sudo().search(
            [
                ("user_id", "=", self._current_user_id()),
                ("pair_key", "=", pair_key),
            ],
            order="sent_at asc, id asc",
        )
        return self._json_response([self._message_payload(message) for message in messages])

    @http.route("/api/v1/messages", type="http", auth="user", methods=["POST"], csrf=False)
    def create_message(self, **kwargs):
        forbidden = self._forbid_cross_origin()
        if forbidden:
            return forbidden
        data = self._json_payload()
        if data is None:
            return self._bad_json()
        sender_contact = self._get_contact(data.get("sender_contact_id")) if data.get("sender_contact_id") else None
        recipient_contact = self._get_contact(data.get("recipient_contact_id")) if data.get("recipient_contact_id") else None
        if not sender_contact and not recipient_contact:
            return self._json_response({"detail": "At least one contact must exist"}, status=404)
        body = self._clean_text(data.get("body"))
        if not body:
            return self._json_response({"detail": "body is required"}, status=400)
        message = request.env["networkpilot.contact_message"].sudo().create(
            {
                "user_id": self._current_user_id(),
                "sender_contact_id": sender_contact.id if sender_contact else False,
                "recipient_contact_id": recipient_contact.id if recipient_contact else False,
                "body": body,
                "message_type": data.get("message_type") or "chat",
                "sent_at": self._parse_datetime(data.get("sent_at")) or fields.Datetime.now(),
                "metadata_json": json.dumps(data.get("metadata_json") or {}, ensure_ascii=False),
                "is_ai_draft": bool(data.get("is_ai_draft")),
            }
        )
        return self._json_response(self._message_payload(message), status=201)

    @http.route("/api/v1/messages/<int:message_id>", type="http", auth="user", methods=["DELETE"], csrf=False)
    def delete_message(self, message_id, **kwargs):
        forbidden = self._forbid_cross_origin()
        if forbidden:
            return forbidden
        message = request.env["networkpilot.contact_message"].sudo().search(
            [
                ("id", "=", message_id),
                ("user_id", "=", self._current_user_id()),
            ],
            limit=1,
        )
        if not message:
            return self._json_response({"detail": "Message not found"}, status=404)
        message.unlink()
        return self._json_response(status=204)

    @http.route("/api/v1/ai/contact-strategy/<int:contact_id>", type="http", auth="user", methods=["GET"], csrf=False)
    def get_contact_strategy(self, contact_id, **kwargs):
        contact = self._get_contact(contact_id)
        if not contact:
            return self._json_response({"detail": "Contact not found"}, status=404)
        interactions = request.env["networkpilot.interaction"].sudo().search(
            [("contact_id", "=", contact.id)],
            order="interaction_date desc, id desc",
            limit=5,
        )
        reminders = request.env["networkpilot.reminder"].sudo().search(
            [
                ("user_id", "=", self._current_user_id()),
                ("contact_id", "=", contact.id),
            ],
            order="due_date asc, id desc",
            limit=3,
        )
        relationships = request.env["networkpilot.contact_relationship"].sudo().search(
            [
                ("user_id", "=", self._current_user_id()),
                "|",
                ("source_contact_id", "=", contact.id),
                ("target_contact_id", "=", contact.id),
            ],
            order="strength desc, last_active_at desc",
            limit=5,
        )
        days_since_last_interaction = None
        if contact.last_interaction_date:
            days_since_last_interaction = (date.today() - contact.last_interaction_date.date()).days
        snapshot = {
            "contact": {
                "id": contact.id,
                "full_name": contact.full_name,
                "first_name": contact.first_name,
                "last_name": contact.last_name or None,
                "company": contact.company or None,
                "role": contact.role or None,
                "importance_level": contact.importance_level,
                "notes": contact.notes or None,
                "email": contact.email or None,
                "phone": contact.phone or None,
                "telegram": contact.telegram or None,
                "linkedin": contact.linkedin or None,
            },
            "days_since_last_interaction": days_since_last_interaction,
            "recent_interactions": [
                {
                    "title": item.title,
                    "type": item.interaction_type,
                    "interaction_date": item.interaction_date,
                    "description": item.description or None,
                }
                for item in interactions
            ],
            "active_reminders": [
                {
                    "title": item.title,
                    "due_date": item.due_date,
                    "status": item.status,
                }
                for item in reminders
            ],
            "relationship_edges": [
                {
                    "pair_key": item.pair_key,
                    "relationship_type": item.relationship_type,
                    "strength": item.strength,
                    "message_count": item.message_count,
                }
                for item in relationships
            ],
        }
        plan = LightweightContactAgent().plan_contact_strategy(snapshot)
        return self._json_response(plan)

    @http.route("/api/v1/ai/business-card-scan", type="http", auth="user", methods=["POST"], csrf=False)
    def scan_business_card(self, **kwargs):
        forbidden = self._forbid_cross_origin()
        if forbidden:
            return forbidden
        data = self._json_payload()
        if data is None:
            return self._bad_json()
        image_base64 = self._clean_text(data.get("image_base64"))
        if not image_base64:
            return self._json_response({"detail": "image_base64 is required"}, status=400)
        try:
            result = LightweightContactAgent().extract_business_card(image_base64)
        except RuntimeError as exc:
            return self._json_response({"detail": str(exc)}, status=503)
        except Exception as exc:
            return self._json_response({"detail": str(exc)}, status=422)
        return self._json_response(result)

    @http.route("/api/v1/ai/parse-unstructured-contact", type="http", auth="user", methods=["POST"], csrf=False)
    def parse_unstructured_contact(self, **kwargs):
        forbidden = self._forbid_cross_origin()
        if forbidden:
            return forbidden
        data = self._json_payload()
        if data is None:
            return self._bad_json()
        raw_text = self._clean_text(data.get("text"))
        if not raw_text:
            return self._json_response({"detail": "text is required"}, status=400)
        try:
            contact = LightweightContactAgent().process_contact_data(raw_text)
            result = json.loads(contact.model_dump_json())
        except RuntimeError as exc:
            return self._json_response({"detail": str(exc)}, status=503)
        except Exception as exc:
            return self._json_response({"detail": str(exc)}, status=422)
        return self._json_response(result)
