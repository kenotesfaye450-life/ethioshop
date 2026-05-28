"""Manual orphaned Cloudinary asset scan/deletion utility."""
from backend.app import create_app
from backend.routes.admin import _cloudinary_public_id_from_url
from backend.models import ProductImage, Request, Order, Refund, SiteSetting
from backend.services.image_service import ImageService


def collect_referenced_ids():
    refs = set()
    for url in [x.image_url for x in ProductImage.query.all()]:
        pid = _cloudinary_public_id_from_url(url)
        if pid:
            refs.add(pid)
    for url in [x.image_url for x in Request.query.all() if x.image_url]:
        pid = _cloudinary_public_id_from_url(url)
        if pid:
            refs.add(pid)
    for order in Order.query.all():
        for url in [order.payment_proof_url, order.additional_proof_url]:
            pid = _cloudinary_public_id_from_url(url)
            if pid:
                refs.add(pid)
    for refund in Refund.query.all():
        pid = _cloudinary_public_id_from_url(refund.additional_evidence_url)
        if pid:
            refs.add(pid)
    pid = _cloudinary_public_id_from_url(SiteSetting.get('owner_image_url'))
    if pid:
        refs.add(pid)
    return refs


def main(delete=False, prefix=""):
    app = create_app()
    with app.app_context():
        refs = collect_referenced_ids()
        import cloudinary.api
        resources = cloudinary.api.resources(max_results=500, prefix=prefix).get("resources", [])
        orphans = [r for r in resources if r.get("public_id") not in refs]
        print(f"Referenced: {len(refs)}")
        print(f"Orphans: {len(orphans)}")
        for r in orphans:
            print(f"- {r.get('public_id')} ({r.get('bytes', 0)} bytes)")
            if delete:
                ImageService.delete_image(r.get("public_id"))
        if delete:
            print("Deleted orphan assets.")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--delete", action="store_true")
    parser.add_argument("--prefix", default="")
    args = parser.parse_args()
    main(delete=args.delete, prefix=args.prefix)
