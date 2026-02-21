import torch
import torch.nn as nn

STUDENT_HIDDEN = 32


class StudentActor(nn.Module):
    def __init__(self, obs_dim, action_dim):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(obs_dim, STUDENT_HIDDEN),
            nn.ReLU(),
            nn.Linear(STUDENT_HIDDEN, STUDENT_HIDDEN),
            nn.ReLU(),
            nn.Linear(STUDENT_HIDDEN, action_dim),
        )

    def forward(self, x):
        return self.net(x)

    def predict(self, obs, action_masks=None, deterministic=True):
        # API Matcher for batched_env
        with torch.no_grad():
            x = torch.as_tensor(obs).float()
            if next(self.parameters()).is_cuda:
                x = x.to(next(self.parameters()).device)

            logits = self.net(x)

            if action_masks is not None:
                # Apply mask (set invalid logits to -inf)
                masks = torch.as_tensor(action_masks, device=logits.device)
                logits[~masks.bool()] = -1e8

            if deterministic:
                actions = torch.argmax(logits, dim=1)
            else:
                probs = torch.softmax(logits, dim=1)
                actions = torch.multinomial(probs, 1).squeeze(1)

            return actions.cpu().numpy(), None
