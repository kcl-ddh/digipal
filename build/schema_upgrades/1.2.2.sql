-- All schema modifications needed to bring 1.2.2b docker databases up to pre-1.7 migration system 

CREATE TABLE "digipal_keyval" (
    "id" serial NOT NULL PRIMARY KEY,
    "key" varchar(300) NOT NULL UNIQUE,
    "val" text,
    "created" timestamp with time zone NOT NULL,
    "modified" timestamp with time zone NOT NULL
)
;

ALTER TABLE digipal_keyval OWNER TO app_digipal;
ALTER TABLE digipal_keyval_id_seq OWNER TO app_digipal;

CREATE TABLE "digipal_text_textpattern" (
    "id" serial NOT NULL PRIMARY KEY,
    "title" varchar(100) NOT NULL UNIQUE,
    "key" varchar(100) NOT NULL UNIQUE,
    "pattern" varchar(1000),
    "order" integer NOT NULL,
    "description" text,
    "created" timestamp with time zone NOT NULL,
    "modified" timestamp with time zone NOT NULL,
    UNIQUE ("key")
)
;

ALTER TABLE digipal_text_textpattern OWNER TO app_digipal;
ALTER TABLE digipal_text_textpattern_id_seq OWNER TO app_digipal;
