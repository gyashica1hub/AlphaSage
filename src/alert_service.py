"""Evaluate persisted alerts and record notification delivery outcomes."""

from datetime import UTC, datetime, timedelta
import logging
import uuid

from src.alert_rules import is_triggered
from src.db.models import Alert, AlertDelivery, User
from src.email_service import send_alert_email

logger = logging.getLogger(__name__)


def evaluate_alerts(session, market_data, send_email: bool = True) -> list[dict]:
    now = datetime.now(UTC)
    results = []
    for alert in session.query(Alert).filter(Alert.active.is_(True)).all():
        user = session.get(User, alert.user_id)
        if user is None:
            continue
        quote = market_data.quote(alert.symbol)
        if not is_triggered(alert.rule, alert.threshold, quote):
            continue
        if alert.last_triggered_at and now - alert.last_triggered_at < timedelta(minutes=alert.cooldown_minutes):
            results.append({"alert_id": alert.id, "symbol": alert.symbol, "status": "cooldown"})
            continue
        value = quote.get("price") if alert.rule.startswith("price_") else quote.get("change_pct")
        message = f"{alert.symbol}: {alert.rule.replace('_', ' ')} {alert.threshold}. Current value: {value}."
        status = "skipped"
        error = None
        if send_email:
            try:
                send_alert_email(user.email, alert.symbol, message)
                status = "sent"
            except Exception as delivery_error:
                status = "failed"
                error = str(delivery_error)
                logger.exception("alert_delivery_failed", extra={"alert_id": alert.id, "symbol": alert.symbol})
        else:
            status = "evaluated"
        alert.last_triggered_at = now
        session.add(AlertDelivery(id=str(uuid.uuid4()), alert_id=alert.id, user_id=user.id, channel="email", status=status, message=message, error=error, created_at=now))
        results.append({"alert_id": alert.id, "symbol": alert.symbol, "status": status, "message": message})
    session.commit()
    return results
