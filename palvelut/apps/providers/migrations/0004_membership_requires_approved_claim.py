from django.db import migrations


FORWARD_SQL = """
CREATE OR REPLACE FUNCTION providers_membership_requires_approved_claim()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM providers_provider
        WHERE id = NEW.provider_id
          AND claim_status = 'approved'
    ) THEN
        RAISE EXCEPTION 'provider membership requires an approved claim'
            USING ERRCODE = '23514';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER providers_membership_requires_approved_claim_trigger
BEFORE INSERT OR UPDATE OF provider_id
ON providers_providermembership
FOR EACH ROW
EXECUTE FUNCTION providers_membership_requires_approved_claim();
"""

REVERSE_SQL = """
DROP TRIGGER IF EXISTS providers_membership_requires_approved_claim_trigger
ON providers_providermembership;
DROP FUNCTION IF EXISTS providers_membership_requires_approved_claim();
"""


class Migration(migrations.Migration):
    dependencies = [
        ("providers", "0003_provider_claim_state"),
    ]

    operations = [
        migrations.RunSQL(FORWARD_SQL, REVERSE_SQL),
    ]
