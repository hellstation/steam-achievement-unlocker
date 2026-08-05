/*
 * Universal (x86_64 + arm64) entry point for the .app bundle.
 * Opens Terminal with a temp .command that runs the PyInstaller binary.
 * On Apple Silicon, prefers arch -x86_64 (Rosetta) when the payload is Intel.
 */
#include <limits.h>
#include <mach-o/dyld.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>
#include <libgen.h>

static int write_cmd(const char *path, const char *bin) {
    FILE *f = fopen(path, "w");
    if (!f) {
        return -1;
    }
    fprintf(f, "#!/bin/bash\n");
    fprintf(f, "clear\n");
    fprintf(f, "BIN=\"%s\"\n", bin);
    fprintf(f, "if [[ ! -x \"$BIN\" ]]; then\n");
    fprintf(f, "  echo \"Не найден бинарник: $BIN\"\n");
    fprintf(f, "  read -r -p \"Нажмите Enter...\"\n");
    fprintf(f, "  exit 1\n");
    fprintf(f, "fi\n");
    fprintf(f, "if [[ \"$(uname -m)\" == \"arm64\" ]]; then\n");
    fprintf(f, "  if arch -x86_64 /usr/bin/true 2>/dev/null; then\n");
    fprintf(f, "    arch -x86_64 \"$BIN\"\n");
    fprintf(f, "    status=$?\n");
    fprintf(f, "  else\n");
    fprintf(f, "    echo \"==============================================\"\n");
    fprintf(f, "    echo \" Нужна Rosetta 2 (приложение собрано под Intel)\"\n");
    fprintf(f, "    echo \" Установите командой:\"\n");
    fprintf(f, "    echo \"   softwareupdate --install-rosetta --agree-to-license\"\n");
    fprintf(f, "    echo \"==============================================\"\n");
    fprintf(f, "    echo\n");
    fprintf(f, "    \"$BIN\"\n");
    fprintf(f, "    status=$?\n");
    fprintf(f, "  fi\n");
    fprintf(f, "else\n");
    fprintf(f, "  \"$BIN\"\n");
    fprintf(f, "  status=$?\n");
    fprintf(f, "fi\n");
    fprintf(f, "echo\n");
    fprintf(f, "read -r -p \"Нажмите Enter чтобы закрыть...\"\n");
    fprintf(f, "exit $status\n");
    fclose(f);
    chmod(path, 0755);
    return 0;
}

int main(void) {
    char exe[PATH_MAX];
    uint32_t size = sizeof(exe);
    if (_NSGetExecutablePath(exe, &size) != 0) {
        return 1;
    }

    char resolved[PATH_MAX];
    if (!realpath(exe, resolved)) {
        strncpy(resolved, exe, sizeof(resolved) - 1);
        resolved[sizeof(resolved) - 1] = '\0';
    }

    /* Copy before dirname mutates */
    char resolved_copy[PATH_MAX];
    strncpy(resolved_copy, resolved, sizeof(resolved_copy) - 1);
    resolved_copy[sizeof(resolved_copy) - 1] = '\0';

    char *macos_dir = dirname(resolved_copy);
    char contents_path[PATH_MAX];
    snprintf(contents_path, sizeof(contents_path), "%s/..", macos_dir);

    char contents_r[PATH_MAX];
    if (!realpath(contents_path, contents_r)) {
        return 1;
    }

    char bin[PATH_MAX];
    snprintf(bin, sizeof(bin), "%s/Resources/bin/SteamAchievementUnlocker", contents_r);

    char cmdpath[] = "/tmp/steam-ach-unlocker-XXXXXX.command";
    int fd = mkstemps(cmdpath, 8); /* keep ".command" suffix */
    if (fd < 0) {
        return 1;
    }
    close(fd);

    if (write_cmd(cmdpath, bin) != 0) {
        return 1;
    }

    char *args[] = {"/usr/bin/open", "-a", "Terminal", cmdpath, NULL};
    execv(args[0], args);
    perror("execv open");
    return 1;
}
