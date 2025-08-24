import { Request, Response } from "express";
import {
    checkEmailAvailable,
    checkUserNameAvailable,
    createUser,
    getUserByUsername,
    removeUser,
} from "./user.service";

import { validateEmail, validateUsername } from "./user.validate";

export async function checkEmail(req: Request, res: Response): Promise<void> {
    try {
        const email = req.body.email?.trim().toLowerCase();
        if (!email || !validateEmail(email)) {
            res.status(400).json({ error: "Bad Request" });
        } else {
            const available = await checkEmailAvailable(email);
            if (available) {
                res.status(200).json({ message: "Email available" });
            } else {
                res.status(409).json({ error: "Email unavailable" });
            }
        }
    } catch (error: any) {
        res.status(500).json({ error: "Unable to check Email availability" });
    }
}

export async function checkUserName(
    req: Request,
    res: Response,
): Promise<void> {
    try {
        const username = req.body.username?.trim().toLowerCase();
        if (!username || !validateUsername(username)) {
            res.status(400).json({ error: "Bad Request" });
        } else {
            const available = await checkUserNameAvailable(username);
            if (available) {
                res.status(200).json({ message: "Username available" });
            } else {
                res.status(409).json({ error: "Username unavailable" });
            }
        }
    } catch (error: any) {
        console.error(error);
        res.status(500).json({
            error: "Unable to check Username availability",
        });
    }
}

export async function createUserController(
    req: Request,
    res: Response,
): Promise<void> {
    try {
        const email = req.body.email?.trim().toLowerCase();
        const username = req.body.username?.trim().toLowerCase();

        if (!email || !username) {
            res.status(400).json({ error: "Missing values" });
            return;
        } else if (!validateEmail(email)) {
            res.status(400).json({ error: "Wrong email" });
        } else if (!validateUsername(username)) {
            res.status(400).json({ error: "Wrong username" });
        } else {
            const newUser = await createUser({
                email: email,
                username: username,
            });
            console.log("created user : ", newUser);
            res.status(201).json({ message: "Account created" });
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
        const username = req.params.username?.trim().toLowerCase();

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
        } else {
            res.status(500).json({ error: "Unable to fetch user" });
        }
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
