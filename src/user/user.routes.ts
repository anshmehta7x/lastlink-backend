import { Router } from "express";
import {
    checkEmail,
    checkUserName,
    createUserController,
    getUserController,
    removeUserController,
} from "./user.controller";

const router: Router = Router();

router.post("/email-available", checkEmail);
router.post("/username-available", checkUserName);
router.post("/create", createUserController);
router.get("/:username", getUserController);
router.delete("/remove", removeUserController);

export default router;
