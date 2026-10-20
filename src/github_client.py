import os
import random
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import requests

try:
    from dotenv import load_dotenv  # type: ignore[import-untyped,import-not-found]
    load_dotenv()
except ImportError:
    pass

GITHUB_API_BASE_URL = "https://api.github.com"

# Palabras clave y tópicos para explorar proyectos variados y curiosos
EXPLORATION_KEYWORDS = [
    "cli", "utility", "tool", "engine", "parser", "bot", "algorithm",
    "generator", "scanner", "api", "simulator", "dashboard", "extension",
    "visualizer", "audio", "terminal", "automation", "minimal", "game",
    "crawler", "framework", "compiler", "monitor", "creative", "agent"
]

POPULAR_LANGUAGES = [
    "python", "javascript", "typescript", "rust", "go",
    "c", "cpp", "csharp", "ruby", "java", "kotlin", "swift"
]


class GitHubAPIError(Exception):
    """Excepción base para errores de la API de GitHub."""
    pass


class RateLimitExceededError(GitHubAPIError):
    """Lanzada cuando se supera el límite de peticiones de GitHub."""
    def __init__(self, reset_time: Optional[datetime] = None, message: str = ""):
        self.reset_time = reset_time
        super().__init__(message)


class GitHubClient:
    """Cliente para interactuar con la API pública de GitHub con búsqueda semi-aleatoria."""

    def __init__(self, token: Optional[str] = None):
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.session = requests.Session()

        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "RandomSearchRepo-CLI/1.0",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        self.session.headers.update(headers)
        self.last_rate_limit: Dict[str, Any] = {}

    def _update_rate_limit_info(self, response: requests.Response) -> None:
        """Extrae las cabeceras de rate limit devueltas por GitHub."""
        limit = response.headers.get("X-RateLimit-Limit")
        remaining = response.headers.get("X-RateLimit-Remaining")
        reset_timestamp = response.headers.get("X-RateLimit-Reset")

        reset_dt = datetime.fromtimestamp(int(reset_timestamp)) if reset_timestamp else None

        self.last_rate_limit = {
            "limit": int(limit) if limit else None,
            "remaining": int(remaining) if remaining else None,
            "reset": reset_dt,
        }

    def check_rate_limit(self) -> Dict[str, Any]:
        """Consulta el estado actual de los límites de tasa de la API."""
        url = f"{GITHUB_API_BASE_URL}/rate_limit"
        response = self.session.get(url)
        if response.status_code == 200:
            data = response.json()
            return data.get("resources", {})
        response.raise_for_status()
        return {}

    def generate_semi_random_query(
        self,
        keyword: Optional[str] = None,
        language: Optional[str] = None,
        min_stars: int = 5,
        max_stars: int = 300,
        randomize_date: bool = True,
    ) -> str:
        """
        Genera una query balanceada y semi-aleatoria para descubrir repositorios interesantes
        evitando proyectos vacíos o forks irrelevantes.
        """
        parts = ["fork:false", "archived:false", "is:public"]

        # Filtro de estrellas: rango acotado para encontrar joyas ocultas o proyectos independientes
        parts.append(f"stars:{min_stars}..{max_stars}")

        # Selección de palabra clave aleatoria si no se especifica una
        chosen_keyword = keyword if keyword is not None else random.choice(EXPLORATION_KEYWORDS)
        if chosen_keyword:
            parts.append(chosen_keyword)

        # Lenguaje opcional
        if language:
            parts.append(f"language:{language}")

        # Rango de fecha aleatorio para diversificar el muestreo temporal (últimos 6 años)
        if randomize_date:
            today = datetime.now()
            random_days_ago = random.randint(30, 365 * 6)
            start_date = (today - timedelta(days=random_days_ago)).strftime("%Y-%m-%d")
            end_date = (today - timedelta(days=max(0, random_days_ago - 180))).strftime("%Y-%m-%d")
            parts.append(f"created:{start_date}..{end_date}")

        return " ".join(parts)

    def search_repositories(
        self,
        query: str,
        page: int = 1,
        per_page: int = 30,
        sort: Optional[str] = None,
        order: str = "desc",
    ) -> Dict[str, Any]:
        """Ejecuta una búsqueda de repositorios contra la API de GitHub."""
        url = f"{GITHUB_API_BASE_URL}/search/repositories"
        params: Dict[str, Any] = {
            "q": query,
            "page": page,
            "per_page": min(per_page, 100),
            "order": order,
        }
        if sort:
            params["sort"] = sort

        response = self.session.get(url, params=params)
        self._update_rate_limit_info(response)

        if response.status_code == 403:
            reset_dt = self.last_rate_limit.get("reset")
            msg = f"Límite de tasa alcanzado en GitHub API. Se reinicia a las {reset_dt}."
            raise RateLimitExceededError(reset_time=reset_dt, message=msg)

        if not response.ok:
            raise GitHubAPIError(
                f"Error en GitHub API [{response.status_code}]: {response.text}"
            )

        return response.json()

    def get_random_repository(
        self,
        language: Optional[str] = None,
        min_stars: int = 5,
        max_stars: int = 500,
        keyword: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Obtiene un repositorio aleatorio utilizando paginación aleatoria y consultas variadas.
        """
        query = self.generate_semi_random_query(
            keyword=keyword,
            language=language,
            min_stars=min_stars,
            max_stars=max_stars,
        )

        # Paso 1: Obtener la primera página para determinar el total de coincidencias
        first_page = self.search_repositories(query=query, page=1, per_page=30)
        total_count = first_page.get("total_count", 0)
        items: List[Dict[str, Any]] = first_page.get("items", [])

        if not items:
            # Fallback simple con una consulta más amplia si no hubo resultados
            fallback_query = f"stars:{min_stars}..{max_stars} fork:false"
            fallback_res = self.search_repositories(query=fallback_query, page=1, per_page=30)
            items = fallback_res.get("items", [])
            if not items:
                return None

        # GitHub Search solo expone los primeros 1,000 resultados (máx página 10 con per_page=30 o 33 páginas)
        max_available_pages = min((total_count // 30) + 1, 10)

        # Si hay más de una página, seleccionamos una página al azar para maximizar entropía
        if max_available_pages > 1:
            random_page = random.randint(1, max_available_pages)
            if random_page != 1:
                page_data = self.search_repositories(query=query, page=random_page, per_page=30)
                items = page_data.get("items", items)

        # Elegir un repositorio al azar dentro de la página elegida
        return random.choice(items) if items else None
