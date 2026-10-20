import io
import os
import sys
from datetime import datetime

# Asegurar compatibilidad de encoding en terminales de Windows
if sys.platform == "win32":
    try:
        if isinstance(sys.stdout, io.TextIOWrapper):
            sys.stdout.reconfigure(encoding="utf-8")
        if isinstance(sys.stderr, io.TextIOWrapper):
            sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from src.github_client import GitHubClient, RateLimitExceededError, GitHubAPIError


def print_banner() -> None:
    print("=" * 60)
    print(" [*] RandomSearchRepo CLI - Descubridor de Repositorios [*] ")
    print("=" * 60)


def print_repo_card(repo: dict) -> None:
    name = repo.get("full_name", "N/A")
    desc = repo.get("description") or "Sin descripcion proporcionada."
    url = repo.get("html_url", "")
    stars = repo.get("stargazers_count", 0)
    forks = repo.get("forks_count", 0)
    lang = repo.get("language") or "No especificado"
    license_info = (repo.get("license") or {}).get("name", "Sin licencia")
    created_at = repo.get("created_at", "")[:10]
    topics = repo.get("topics", [])

    print("\n[+] REPOSITORIO ENCONTRADO:")
    print(f"  * Nombre:       {name}")
    print(f"  * Lenguaje:     {lang}")
    print(f"  * Estrellas:    {stars} | Forks: {forks}")
    print(f"  * Creado el:    {created_at}")
    print(f"  * Licencia:     {license_info}")
    if topics:
        print(f"  * Topicos:      {', '.join(topics)}")
    print(f"  * Enlace:       {url}")
    print(f"  * Descripcion:  {desc}\n")



def main() -> None:
    print_banner()

    client = GitHubClient()

    print("[*] Verificando conexión con la API de GitHub...")
    try:
        rate_limits = client.check_rate_limit()
        search_limit = rate_limits.get("search", {})
        print(f"[+] Conexión exitosa!")
        print(f"    - Límite de búsquedas: {search_limit.get('remaining')}/{search_limit.get('limit')} disponibles")
        reset_epoch = search_limit.get("reset")
        if reset_epoch:
            reset_time = datetime.fromtimestamp(reset_epoch).strftime("%H:%M:%S")
            print(f"    - Reinicio de cuota:   {reset_time}")

    except Exception as e:
        print(f"[-] Error al consultar estado de la API: {e}")
        sys.exit(1)

    print("\n[*] Generando búsqueda semi-aleatoria de repositorios poco conocidos...")
    try:
        repo = client.get_random_repository(min_stars=5, max_stars=300)
        if repo:
            print_repo_card(repo)
        else:
            print("[!] No se encontraron repositorios con los filtros aleatorios actuales. Prueba de nuevo.")

        # Mostrar cuota restante actualizada
        if client.last_rate_limit:
            remaining = client.last_rate_limit.get("remaining")
            limit = client.last_rate_limit.get("limit")
            print(f"[i] Cuota de búsqueda restante: {remaining}/{limit}")

    except RateLimitExceededError as e:
        print(f"\n[!] Rate Limit alcanzado: {e}")
        print("    Tip: Puedes configurar un GITHUB_TOKEN en tu entorno o archivo .env para aumentar la cuota.")
    except GitHubAPIError as e:
        print(f"\n[-] Error de API: {e}")
    except Exception as e:
        print(f"\n[-] Error inesperado: {e}")


if __name__ == "__main__":
    main()
