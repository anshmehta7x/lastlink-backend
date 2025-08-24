import { Request, Response } from "express";
import {
    createLink,
    deleteLink,
    getLinksByUsername,
    updateLink,
} from "./link.service";
import { validateURL } from "./link.validate";

export async function getLinks(req: Request, res: Response): Promise<void> {
    try {
        const { username } = req.params;

        if (!username) {
            res.status(400).json({ error: "Bad Request" });
            return;
        }

        const data = await getLinksByUsername(username);
        res.status(200).json(data);
    } catch (error: any) {
        if (error.message === "No links found") {
            res.status(404).json({ error: error.message });
        } else {
            res.status(500).json({ error: error.message });
        }
    }
}

export async function createLinkController(
    req: Request,
    res: Response,
): Promise<void> {
    try {
        const { display_text, url, owner } = req.body;

        if (!display_text || !url || !owner) {
            res.status(400).json({ error: "Missing values" });
            return;
        }
        if (!validateURL(url)) {
            res.status(400).json({ error: "URL is not valid" });
            return;
        }

        const newLink = await createLink({ display_text, url, owner });
        res.status(201).json(newLink);
    } catch (error: any) {
        res.status(500).json({ error: "Error creating link" });
    }
}

export async function updateLinkController(
    req: Request,
    res: Response,
): Promise<void> {
    try {
        const { linkId } = req.params;
        const { display_text, url } = req.body;

        if (!linkId) {
            res.status(400).json({ error: "Bad Request" });
            return;
        }

        if (!display_text && !url) {
            res.status(400).json({ error: "No update values provided" });
            return;
        }

        if (url && !validateURL(url)) {
            res.status(400).json({ error: "URL is not valid" });
            return;
        }

        const updatedLink = await updateLink(linkId, { display_text, url });
        res.status(200).json(updatedLink);
    } catch (error: any) {
        if (error.message === "Link not found") {
            res.status(404).json({ error: error.message });
        } else {
            res.status(500).json({ error: "Error updating link" });
        }
    }
}

export async function deleteLinkController(
    req: Request,
    res: Response,
): Promise<void> {
    try {
        const { linkId } = req.params;

        if (!linkId) {
            res.status(400).json({ error: "Bad Request" });
            return;
        }

        const deletedLink = await deleteLink(linkId);
        res.status(200).json({
            message: "Link removed successfully",
            link: deletedLink,
        });
    } catch (error: any) {
        if (error.message === "Link not found") {
            res.status(404).json({ error: error.message });
        } else {
            res.status(500).json({ error: "Error deleting link" });
        }
    }
}
