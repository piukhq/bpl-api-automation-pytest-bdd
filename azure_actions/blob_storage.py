import os

from datetime import datetime

from azure.storage.blob import BlobClient, BlobType, ContentSettings

from settings import BLOB_IMPORT_CONTAINER, BLOB_STORAGE_DSN, REPORT_CONTAINER, REPORT_DIRECTORY, logger


def upload_report_to_blob_storage(filename: str, blob_prefix: str = "bpl") -> str:
    blob_name = f"{blob_prefix}-{datetime.now().strftime('%Y%m%d-%H%M%S')}.html"
    blob_path = os.path.join(REPORT_DIRECTORY, blob_name)
    logger.info(f"Uploading test report: {blob_path} to blob storage")
    blob = BlobClient.from_connection_string(
        conn_str=BLOB_STORAGE_DSN,
        container_name=REPORT_CONTAINER,
        blob_name=blob_path,
    )
    with open(filename, "rb") as f:
        blob.upload_blob(f, content_settings=ContentSettings(content_type="text/html"))

    return blob.url


def upload_voucher_update_to_blob_storage(retailer_slug: str) -> str:
    blob_name = "test_import.csv"
    blob_path = os.path.join(retailer_slug, "voucher-updates", blob_name)
    today_date = datetime.now().strftime("%Y-%m-%d")
    content = f"A2eYRbcvF9yYpW2,{today_date},redeemed\n08oVk3czC9QYLBJ,{today_date},cancelled\n"
    content_binary = content.encode("utf-8")
    blob = BlobClient.from_connection_string(
        conn_str=BLOB_STORAGE_DSN,
        container_name=BLOB_IMPORT_CONTAINER,
        blob_name=blob_path,
    )

    logger.info(f"Uploading test report: {blob_path} to blob storage")
    blob.upload_blob(
        content_binary,
        blob_type=BlobType.BlockBlob,
        overwrite=True,
        content_settings=ContentSettings(content_type="text/csv"),
    )

    return blob.url
