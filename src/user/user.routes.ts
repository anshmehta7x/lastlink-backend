import { Router } from "express";
import {
    checkEmail,
    checkUserName,
    createUserController,
} from "./user.controller";

const router: Router = Router();

router.post("/email-available", checkEmail);
router.post("/username-available", checkUserName);
router.post("/create", createUserController);

export default router;
