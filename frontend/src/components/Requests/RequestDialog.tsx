import React from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "../ui/dialog";
import { Textarea } from "../ui/textarea";
import { Button } from "../ui/button";

type RequestDialogProps = {
  isOpen: boolean;
  onClose: () => void;
  comment: string;
  setComment: React.Dispatch<React.SetStateAction<string>>;
  onConfirm: () => void;
};

const RequestDialog: React.FC<RequestDialogProps> = ({
  isOpen,
  onClose,
  comment,
  setComment,
  onConfirm,
}) => (
  <Dialog open={isOpen} onOpenChange={onClose}>
    <DialogContent className="bg-card">
      <DialogHeader>
        <DialogTitle>Add Comment</DialogTitle>
      </DialogHeader>
      <div className="space-y-4">
        <Textarea
          placeholder="Enter your comment..."
          value={comment}
          onChange={(e) => setComment(e.target.value)}
          className="bg-muted"
        />
      </div>
      <DialogFooter>
        <Button
          onClick={() => {
            onClose();
          }}
          variant="outline"
        >
          Cancel
        </Button>
        <Button
          onClick={onConfirm}
          className="bg-green-400 text-primary-foreground hover:bg-green-400 text-white"
        >
          Confirm
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
);

export default RequestDialog;
