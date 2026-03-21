import secrets
import string


class PasswordGenerator:
    """
    Generador de contraseñas criptográficamente seguro.
    Utiliza el módulo 'secrets' nativo de Python para acceder a la entropía del SO.
    """

    # Caracteres disponibles
    UPPERCASE = string.ascii_uppercase
    LOWERCASE = string.ascii_lowercase
    DIGITS = string.digits
    SYMBOLS = "!@#$%^&*()-_=+[]{}|;:,.<>?"

    @classmethod
    def generate(
        cls,
        length: int = 16,
        use_upper: bool = True,
        use_lower: bool = True,
        use_digits: bool = True,
        use_symbols: bool = True,
    ) -> str:
        """
        Genera una contraseña segura garantizando al menos un carácter
        de cada conjunto seleccionado.
        """
        if length < 8:
            raise ValueError(
                "Por seguridad, la longitud mínima debe ser de 8 caracteres."
            )

        pool = ""
        guaranteed_chars = []

        # Se asegura al menos un carácter por regla
        if use_upper:
            pool += cls.UPPERCASE
            guaranteed_chars.append(secrets.choice(cls.UPPERCASE))

        if use_lower:
            pool += cls.LOWERCASE
            guaranteed_chars.append(secrets.choice(cls.LOWERCASE))

        if use_digits:
            pool += cls.DIGITS
            guaranteed_chars.append(secrets.choice(cls.DIGITS))

        if use_symbols:
            pool += cls.SYMBOLS
            guaranteed_chars.append(secrets.choice(cls.SYMBOLS))

        if not pool:
            raise ValueError("Debe seleccionar al menos un tipo de carácter.")

        # Se rellena la longitud requerida de forma aleatoria desde el pool
        remaining_length = length - len(guaranteed_chars)
        random_chars = [secrets.choice(pool) for _ in range(remaining_length)]

        # Se unen los caracteres garantizados con los aleatorios
        password_list = guaranteed_chars + random_chars

        # Se mezcla la lista de forma segura
        secure_random = secrets.SystemRandom()
        secure_random.shuffle(password_list)

        return "".join(password_list)
