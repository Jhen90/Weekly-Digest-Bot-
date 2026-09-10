import pytest
from unittest.mock import patch, MagicMock
from src.pulse.mailer import send_email

def test_send_email_success():
    """Test successful email send."""
    with patch("src.pulse.mailer.smtplib.SMTP") as mock_smtp:
        mock_context = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_context

        result = send_email(
            html="<html><body>Test</body></html>",
            text="Test",
            subject="Test Digest",
            sender="test@gmail.com",
            recipient="user@example.com",
            app_password="test-password",
        )

        assert result is True
        mock_context.starttls.assert_called_once()
        mock_context.login.assert_called_once_with("test@gmail.com", "test-password")
        mock_context.send_message.assert_called_once()

def test_send_email_auth_error():
    """Test authentication error handling."""
    with patch("src.pulse.mailer.smtplib.SMTP") as mock_smtp:
        mock_context = MagicMock()
        mock_context.login.side_effect = Exception("Authentication failed")
        mock_smtp.return_value.__enter__.return_value = mock_context

        with pytest.raises(Exception):
            send_email(
                html="<html></html>",
                text="Test",
                subject="Test",
                sender="test@gmail.com",
                recipient="user@example.com",
                app_password="bad-password",
            )
