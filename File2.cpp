#include "sl.h"
#include <cstdlib>
#include <sqlite3.h>
#include <sstream>
#include <string>
#include <unistd.h>
#include <vector>

#include "nmea.h"

const int WIN_WIDTH = 480, WIN_HEIGHT = 320, FPS = 30;
const std::string DB_FILENAME = "C:/ais/ais.db";
std::vector<std::string> split(const char *str, char c = ',')
{
    std::vector<std::string> result;

    do
    {
        const char *begin = str;

        while (*str != c && *str)
            str++;

        result.push_back(std::string(begin, str));
    } while (0 != *str++);

    return result;
}
int irnd(int m)
{

    return rand() % m;
}

const char double2str(double value)
{
    char buffer[64];
    int ret = snprintf(buffer, sizeof buffer, "%f", value);

    if (ret < 0)
    {
        return EXIT_FAILURE;
    }
    if (ret >= sizeof buffer)
    {
    }
    return ret;
}

static int cb(void *NotUsed, int argc, char **argv, char **azColName)
{
    int i;
    std::string str1("data");
    for (i = 0; i < argc; i++)
    {
        //printf("%s = %s\n", azColName[i], argv[i] ? argv[i] : "NULL");
        if (str1.compare(azColName[i]) == 0)
        {
            decode_nmea(argv[i]);
        }
    }
    // printf("\n");
    return 0;
}

int main(int args, char *argv[])
{
    sqlite3 *db;
    char *zErrMsg = 0;
    int rc;
    std::string sql;

    // open db
    rc = sqlite3_open(DB_FILENAME.c_str(), &db);
    if (rc)
    {
        fprintf(stderr, "Can't open database: %s\n", sqlite3_errmsg(db));
        return (0);
    }
    else
    {
        fprintf(stderr, "Opened database successfully\n");
    }

    // get data from db
    sql = "SELECT data FROM rawdata ORDER BY id asc limit 10;";
    rc = sqlite3_exec(db, sql.c_str(), cb, 0, &zErrMsg);

    if (rc != SQLITE_OK)
    {
        fprintf(stderr, "SQL error: %s\n", zErrMsg);
        sqlite3_free(zErrMsg);
    }
    else
    {
        fprintf(stdout, "Query executed successfully\n");
    }

    // close up db
    sqlite3_close(db);
    return 0;
    // set up our window and a few resources we need
    slWindow(WIN_WIDTH, WIN_HEIGHT, "AIS beta", false);
    slSetFont(slLoadFont("arial.ttf"), 24);
    slSetTextAlign(SL_ALIGN_LEFT);
    slSetForeColor(0.9, 0.9, 0.0, 1.0);

    while (!slShouldClose() && !slGetKey(SL_KEY_ESCAPE))

    {
        for (int i = 0; i < 20; i++)
            slLine(irnd(WIN_WIDTH), irnd(WIN_HEIGHT), irnd(WIN_WIDTH), irnd(WIN_HEIGHT));
        double dt = slGetDeltaTime();
        double t = slGetTime();
        std::string str1 = std::to_string(dt);
        std::string str2 = std::to_string(t);
        slText(20, 100, str1.c_str());
        slText(20, 80, str2.c_str());

        slRender();
        // usleep(250000);
    }
    slClose();

    return 0;
}