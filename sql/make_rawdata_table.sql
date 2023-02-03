DROP TABLE IF EXISTS "rawdata";
CREATE TABLE "rawdata" (
    "id" INTEGER NOT NULL,
    "data" TEXT(80),
    "tm" integer NOT NULL,
    PRIMARY KEY ("id")
);