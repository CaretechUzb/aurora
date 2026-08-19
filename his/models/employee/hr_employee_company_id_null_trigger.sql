-- Trigger function to set company_id to NULL on update
CREATE OR REPLACE FUNCTION set_company_id_null()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.company_id IS DISTINCT FROM OLD.company_id THEN
        NEW.company_id := NULL;
    END IF;
    RETURN NEW;
END
$$
LANGUAGE plpgsql;

-- Trigger faqat mavjud bo'lmasa yaratilsin
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'trg_set_company_id_null') THEN
        CREATE TRIGGER trg_set_company_id_null
        BEFORE UPDATE OF company_id ON hr_employee
        FOR EACH ROW
        EXECUTE FUNCTION set_company_id_null();
    END IF;
END
$$;
