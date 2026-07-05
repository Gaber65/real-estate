import logging
import re

from functools import wraps

from psycopg2 import IntegrityError

from ..helpers.global_response import GlobalResponse

from odoo.exceptions import (
    ValidationError,
    UserError
)


_logger = logging.getLogger(__name__)


def api_exception_handler(func):
    @wraps(func)
    def wrapper(*args, **kwargs):

        try:
            return func(*args, **kwargs)

        except ValidationError as e:

            return GlobalResponse.error(
                
                message="Validation failed",
                errors=[str(e)],
                status=400,
            )

        except UserError as e:

            return GlobalResponse.error(
                
                message="Business rule violation",
                errors=[str(e)],
                status=400,
            )



        except IntegrityError as e:

            error_message = str(e)

            # UNIQUE CONSTRAINT
            if "duplicate key value violates unique constraint" in error_message.lower():

                field_match = re.search(
                    r'Key \((.*?)\)=\((.*?)\)',
                    error_message
                )

                if field_match:
                    field_name = field_match.group(1)
                    field_value = field_match.group(2)

                    return GlobalResponse.error(
                        message="Duplicate value",
                        errors=[
                            f"'{field_name}' value '{field_value}' already exists."
                        ],
                        status=409,
                    )

                return GlobalResponse.error(
                    message="Duplicate value",
                    errors=["A record with the same unique value already exists."],
                    status=409,
                )

            # FOREIGN KEY
            if "foreign key" in error_message.lower():

                field_match = re.search(
                    r'Key \((.*?)\)=\((.*?)\)',
                    error_message
                )

                if field_match:
                    field_name = field_match.group(1)
                    field_value = field_match.group(2)
                    field_mapping = {
                        'owner_id': 'Owner',
                        'tag_id': 'Tag',
                        'property_id': 'Property',
                    }
                    display_name = field_mapping.get(
                        field_name,
                        field_name
                    )
                    return GlobalResponse.error(
                        
                        message="Related record does not exist",
                        errors=[
                            f"{display_name} with id '{field_value}' was not found."
                        ],
                        status=400,
                    )

                return GlobalResponse.error(
                    
                    message="Related record does not exist",
                    errors=["Referenced record does not exist."],
                    status=400,
                )

            # NOT NULL
            if (
                    "not-null constraint" in error_message.lower()
                    or "null value in column" in error_message.lower()
            ):
                field_match = re.search(
                    r'column "(.*?)"',
                    error_message
                )

                field_name = field_match.group(1) if field_match else "field"

                return GlobalResponse.error(
                    
                    message="Required field missing",
                    errors=[
                        f"'{field_name}' is required."
                    ],
                    status=400,
                )

            return GlobalResponse.error(
                
                message="Database error",
                errors=[error_message],
                status=400,
            )

        except TypeError as e:

            return GlobalResponse.error(
                
                message="Invalid request data",
                errors=[str(e)],
                status=400,
            )

        except ValueError as e:

            return GlobalResponse.error(
                
                message="Invalid request data",
                errors=[str(e)],
                status=400,
            )

        except Exception as e:

            _logger.exception(
                "Unexpected error in API %s",
                func.__name__
            )

            return GlobalResponse.error(
                
                message="Internal server error",
                errors=[str(e)],
                status=500,
            )

    return wrapper
