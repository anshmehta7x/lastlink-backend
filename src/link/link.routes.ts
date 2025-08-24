import { Router } from "express";
import {
    getLinks,
    createLinkController,
    deleteLinkController,
    updateLinkController,
} from "./link.controller";

const router: Router = Router();

router.get("/:username", getLinks);
router.post("/", createLinkController);
router.put("/:linkId", updateLinkController);
router.delete("/:linkId", deleteLinkController);

export default router;
