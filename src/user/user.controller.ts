import { Request, Response } from "express";
import {
    checkEmailAvailable,
    checkUserNameAvailable,
    createUser,
    getUserByUsername,
    removeUser,
} from "./user.service";

import { validateEmail, validateUsername } from "./validate";

export async function checkEmail(req: Request, res: Response): Promise<void> {
    try {
        if (req.body.email === null || !validateEmail(req.body.email)) {
            res.status(400).json({ message: "Bad Request" });
        } else {
            const available = await checkEmailAvailable(req.body.email);
            if (available) {
                res.status(200).json({ message: "Email available" });
            } else {
                res.status(409).json({ message: "Email unavailable" });
            }
        }
    } catch (error: any) {
        res.status(500).json({ error: "Unable to check Email availablity" });
    }
}

export async function checkUserName(
    req: Request,
    res: Response,
): Promise<void> {
    try {
        if (
            req.body.username === null ||
            !validateUsername(req.body.username)
        ) {
            res.status(400).json({ message: "Bad Request" });
        } else {
            const available = await checkUserNameAvailable(req.body.username);
            if (available) {
                res.status(200).json({ message: "Username available" });
            } else {
                res.status(409).json({ message: "Username unavailable" });
            }
        }
    } catch (error: any) {
        console.error(error);
        res.status(500).json({ error: "Unable to check Username availablity" });
    }
}

export async function createUserController(
    req: Request,
    res: Response,
): Promise<void> {
    try {
        if (!req.body || !req.body.email || !req.body.username) {
            res.status(400).json({ error: "Missing values" });
            return;
        } else if (!validateEmail(req.body.email)) {
            res.status(400).json({ error: "Wrong email" });
        } else if (!validateUsername(req.body.username)) {
            res.status(400).json({ error: "Wrong username" });
        } else {
            const newUser = await createUser({
                email: req.body.email,
                username: req.body.username,
            });
            console.log("creAted user : ", newUser);
            res.status(201).json({ message: "Account creAted" });
        }
    } catch (error: any) {
        if (error.message === "Email taken") {
            res.status(409).json({ error: "Email unavailable" });
        } else if (error.message === "Username taken") {
            res.status(409).json({ error: "Username unavailable" });
        } else if (error.message === "Error creating account") {
            res.status(500).json({ error: "Error creating account" });
        } else {
            res.status(500).json({ error: error.message });
        }
    }
}

export async function getUserController(
    req: Request,
    res: Response,
): Promise<void> {
    try {
        const { username } = req.params;

        if (!username || !validateUsername(username)) {
            res.status(400).json({ error: "Bad Request" });
            return;
        }

        const user = await getUserByUsername(username);
        if (!user) {
            res.status(404).json({ error: "User not found" });
            return;
        }

        res.status(200).json(user);
    } catch (error: any) {
        console.error(error);
        if (error.message === "Username not found") {
            res.status(404).json({ error: error.message });
        }
        res.status(500).json({ error: "Unable to fetch user" });
    }
}

export async function removeUserController(
    req: Request,
    res: Response,
): Promise<void> {
    try {
        const { id } = req.body;

        if (!id || typeof id !== "number") {
            res.status(400).json({ error: "Bad Request" });
            return;
        }
        const removedUser = await removeUser(id);
        res.status(200).json({
            message: "User removed successfully",
            user: removedUser,
        });
    } catch (error: any) {
        console.error(error);
        if (error.message === "User not found") {
            res.status(404).json({ error: error.message });
        } else {
            res.status(500).json({ error: "Unable to remove user" });
        }
    }
}
